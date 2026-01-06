# app/services/order_services.py
import os
import asyncio
import hashlib
import time
from uuid import UUID
from fastapi import Request
from fastapi.responses import JSONResponse
import grpc

from .order_helpers import create_problem_response
from database import pydantic_models
from repositories.orders_repository import OrderRepository
from database.database_models import OrderDB, OrderStatus
from decorators.order_services_decorators import OrderServiceDecorators
from .orders_grpc_client import PaymentGRPCClient
from opentelemetry import trace
from optl.trace_decorator import trace_service_operation
from cache.cache_service import cache_service

class OrderService:
    def __init__(self, logger, db_session):
        self.logger = logger
        self.order_repo = OrderRepository(db_session)
        self.payment_client = PaymentGRPCClient(logger)
        self.tracer = trace.get_tracer(__name__)
        self._payment_failure_count = 0
        self._circuit_open = False
    
    @OrderServiceDecorators.handle_create_order_errors
    @trace_service_operation("create_order")
    async def create_order(self, request, order_data, user_id, referral_code):
        if not order_data.items:
            return create_problem_response(
                status_code=400,
                error_type="bad-request",
                title="Bad Request",
                detail="Cannot create order with empty items",
                instance=str(request.url)
            )
        
        total = sum(item.quantity * item.unit_price for item in order_data.items)
        
        items_dict = [
            {
                'product_id': item.product_id,
                'name': item.name,
                'quantity': item.quantity,
                'unit_price': item.unit_price
            }
            for item in order_data.items
        ]
        
        order_db = OrderDB(
            user_id=user_id,
            status=OrderStatus.CREATED,
            total=total,
            billing_address_id=order_data.billing_address_id,
            shipping_address_id=order_data.shipping_address_id,
            payment_method_token=order_data.payment_method_token,
            items=items_dict
        )
        
        created_order = await self.order_repo.create_order(order_db)
        
        try:
            payment = await self._create_payment(
                order_id=str(created_order.id),
                amount=created_order.total,
                user_id=user_id,
                payment_method_token=order_data.payment_method_token,
                referral_code=referral_code
            )
            payment_id = payment.payment_id
            await self.order_repo.update_order_payment_id(created_order.id, payment_id)
            await self.order_repo.update_order_status(created_order.id, OrderStatus.PENDING)
            
            order_dict = created_order.to_dict()
            order_dict['client_secret'] = payment.client_secret
            order_dict['payment_id'] = payment_id
            order_dict['status'] = OrderStatus.PENDING.value
            order_dict['checkout_url'] = payment.checkout_url

            if cache_service.enabled:
                await cache_service.set_order(str(created_order.id), order_dict)
            
            return self._build_order_response(order_dict)
            
        except Exception as payment_error:
            await self.order_repo.update_order_status(created_order.id, OrderStatus.FAILED)
            raise Exception(f"Order creation failed: Payment processing error. Order {created_order.id} marked as failed.")
    
    @OrderServiceDecorators.handle_get_order_errors
    @OrderServiceDecorators.validate_order_ownership
    @trace_service_operation("get_order")
    async def get_order(self, request, order_uuid, user_id, order_db):
        if isinstance(order_db, dict):
            order_dict = order_db
        else:
            order_dict = order_db.to_dict()
        self.logger.info(f"order_dict: {order_dict}")
        return self._build_order_response(order_dict)
    
    @OrderServiceDecorators.handle_list_orders_errors
    @trace_service_operation("list_orders")
    async def list_orders(self, request, user_id, query_params):
        skip = (query_params.page - 1) * query_params.page_size
        
        orders_data = await self.order_repo.list_orders(user_id, skip, query_params.page_size)
        total_count = await self.order_repo.count_orders(user_id)
        
        orders_with_items = []
        for order_dict in orders_data:
            order_response = self._build_order_response(order_dict)
            orders_with_items.append(order_response)
        
        order_list = pydantic_models.OrderList(
            items=orders_with_items,
            total=total_count,
            page=query_params.page,
            page_size=query_params.page_size
        )
        
        return order_list
    
    async def _create_payment(self, order_id, amount, user_id, payment_method_token, referral_code=None):
        if self._circuit_open:
            raise Exception("Payment service unavailable (circuit breaker open)")
        
        max_retries = 3
        base_delay = 1
        
        for attempt in range(max_retries):
            try:
                payment = await self.payment_client.create_payment(
                    order_id=order_id,
                    amount=amount,
                    user_id=user_id,
                    payment_method_token=payment_method_token,
                    checkout_mode=os.getenv("PAYMENT_CHECKOUT_MODE", "true").lower() == "true",
                    success_url=os.getenv("PAYMENT_SUCCESS_URL"),
                    cancel_url=os.getenv("PAYMENT_CANCEL_URL"),
                    referral_code=referral_code
                )
                self._payment_failure_count = 0
                self._circuit_open = False
                return payment
                
            except grpc.RpcError as e:
                self._payment_failure_count += 1
                
                if self._payment_failure_count >= 5:
                    self._circuit_open = True
                
                if attempt == max_retries - 1:
                    raise Exception(f"Payment failed after {max_retries} attempts: {e.details()}")
                
                delay = base_delay * (2 ** attempt)
                await asyncio.sleep(delay)
                
            except Exception as e:
                self._payment_failure_count += 1
                
                if self._payment_failure_count >= 5:
                    self._circuit_open = True
                
                if attempt == max_retries - 1:
                    raise Exception(f"Payment failed after {max_retries} attempts: {str(e)}")
                
                delay = base_delay * (2 ** attempt)
                await asyncio.sleep(delay)
        
        raise Exception(f"Payment processing failed")
    async def _is_duplicate_request(self, idempotency_key: str) -> bool:
        if not hasattr(self, '_processed_keys'):
            self._processed_keys = set()
        return idempotency_key in self._processed_keys
    
    async def _store_idempotency_key(self, idempotency_key: str):
        if not hasattr(self, '_processed_keys'):
            self._processed_keys = set()
        self._processed_keys.add(idempotency_key)

    def _build_order_response(self, order_dict):
        items_dict = order_dict.get('items', [])
        
        order_items = [
            pydantic_models.OrderItemResponse(
                product_id=item['product_id'],
                name=item['name'],
                quantity=item['quantity'],
                unit_price=item['unit_price'],
            ) for item in items_dict
        ]
        order_response = pydantic_models.OrderResponse(
            id=order_dict['id'],
            status=order_dict['status'],
            total=order_dict['total'],
            items=order_items,
            billing_address_id=order_dict.get('billing_address_id'),
            shipping_address_id=order_dict.get('shipping_address_id'),
            payment_id=order_dict.get('payment_id'),
            created_at=order_dict.get('created_at'),
            receipt_url=order_dict.get('receipt_url'),
            client_secret=order_dict.get('client_secret'),
            checkout_url=order_dict.get('checkout_url')
        )
       
        return order_response
    
    @OrderServiceDecorators.handle_payment_webhook_errors
    @trace_service_operation("handle_payment_webhook")
    async def handle_payment_webhook(self, request, payment_data: dict):
        idempotency_key = request.headers.get("X-Idempotency-Key")
        
        if idempotency_key and await self._is_duplicate_request(idempotency_key):
            self.logger.info(f"Ignoring duplicate request: {idempotency_key}")
            return {"status": "ignored", "reason": "duplicate"}
        
        order_id = payment_data.get("order_id")
        status = payment_data.get("status")
        if not order_id or not status:
            raise Exception("Missing order_id or status")
        
        order_uuid = UUID(order_id)
        order = await self.order_repo.get_order_by_id(order_uuid)

        if not order:
            raise Exception(f"Order not found: {order_id}")
        
        status_mapping = {
            "succeeded": OrderStatus.PAID,
            "failed": OrderStatus.PENDING,
            "refunded": OrderStatus.CANCELED,
            "canceled": OrderStatus.CANCELED,
            "created" : OrderStatus.PENDING
        }
        
        order_status = status_mapping.get(status)
        if not order_status:
            raise Exception(f"Unknown status: {status}")
        if order.status == order_status:
            return {"status": "ignored", "reason": "already_in_state"}
        
        receipt_url = payment_data.get("receipt_url")
        checkout_url = payment_data.get("checkout_url")
        if order.status == OrderStatus.PAID and order_status == OrderStatus.CREATED:
            return {"status": "ignored", "reason": "invalid_transition"}            
        await self.order_repo.update_order_status(order.id, order_status)
        await self.order_repo.update_order_receipt_url(order.id, receipt_url)
        await self.order_repo.update_order_checkout_url(order.id, checkout_url)
        
        if idempotency_key:
            await self._store_idempotency_key(idempotency_key)
        
        self.logger.info(f"Updated order {order_id} to {order_status.value}")
        
        return {"status": "success", "order_id": order_id, "updated_status": order_status.value}
        