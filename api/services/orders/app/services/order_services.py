from .order_helpers import create_problem_response
from fastapi import Request
from fastapi.responses import JSONResponse
from database import pydantic_models
from datetime import datetime
from uuid import UUID
from repositories.orders_repository import OrderRepository
from database.database_models import OrderDB, OrderStatus
from decorators.order_services_decorators import OrderServiceDecorators
from .orders_grpc_client import PaymentGRPCClient
import grpc
import asyncio
import hashlib
import time
from opentelemetry import trace
from optl.trace_decorator import trace_service_operation

class OrderService:
    def __init__(self, logger, db_session):
        self.logger = logger
        self.order_repo = OrderRepository(db_session)
        self.payment_client = PaymentGRPCClient()
        self._processed_keys = set()
        self.tracer = trace.get_tracer(__name__)
        self._payment_failure_count = 0
        self._circuit_open = False

    @trace_service_operation("create_payment")
    async def _create_payment(self, order_id, amount, user_id, payment_method_token):
        if self._circuit_open:
            self.logger.error("Payment creation failed: Circuit breaker open - payments service unavailable")
            raise Exception("Circuit breaker open - payments service unavailable")
        
        max_retries = 3
        base_delay = 1
        
        for attempt in range(max_retries):
            try:
                with self.tracer.start_as_current_span(f"payment-attempt-{attempt+1}"):
                    payment = await self.payment_client.create_payment(
                        order_id=order_id,
                        amount=amount,
                        user_id=user_id,
                        payment_method_token=payment_method_token
                    )
                    self._payment_failure_count = 0
                    self._circuit_open = False
                    return payment
                    
            except grpc.RpcError as e:
                self._payment_failure_count += 1
                
                if self._payment_failure_count >= 5:
                    self._circuit_open = True
                    self.logger.warning("Payment circuit breaker OPEN - too many failures")
                
                self.logger.error(f"Payment creation failed: {e.code().name} - {e.details()}")
                
                if attempt == max_retries - 1:
                    raise Exception(f"Payment failed after {max_retries} attempts: {e.details()}")
                
                delay = base_delay * (2 ** attempt)
                self.logger.warning(f"Payment attempt {attempt+1} failed, retrying in {delay}s")
                await asyncio.sleep(delay)
                
            except Exception as e:
                self._payment_failure_count += 1
                
                if self._payment_failure_count >= 5:
                    self._circuit_open = True
                    self.logger.warning("Payment circuit breaker OPEN - too many failures")
                
                self.logger.error(f"Payment creation failed: {e}")
                
                if attempt == max_retries - 1:
                    raise Exception(f"Payment failed after {max_retries} attempts: {str(e)}")
                
                delay = base_delay * (2 ** attempt)
                self.logger.warning(f"Payment attempt {attempt+1} failed, retrying in {delay}s")
                await asyncio.sleep(delay)
        
        raise Exception(f"Payment processing failed")

    def _build_order_response(self, order_db, items_dict):
        order_items = [
            pydantic_models.OrderItemResponse(
                product_id=item['product_id'],
                name=item['name'],
                quantity=item['quantity'],
                unit_price=item['unit_price'],
            ) for item in items_dict
        ]

        created_at = order_db.created_at if order_db.created_at else datetime.utcnow()

        return pydantic_models.OrderResponse(
            id=str(order_db.id),
            status=order_db.status,
            total=order_db.total,
            items=order_items,
            billing_address_id=order_db.billing_address_id,
            shipping_address_id=order_db.shipping_address_id,
            payment_id=order_db.payment_id,
            created_at=created_at.isoformat(),
            client_secret=order_db.client_secret,
            receipt_url=order_db.receipt_url
        )

    @trace_service_operation("get_client_secret_with_retry")
    async def _get_client_secret_with_retry(self, payment_id: str, max_attempts: int = 5) -> str:
        for attempt in range(1, max_attempts + 1):
            try:
                payment_info = await self.payment_client.get_payment(payment_id)
                client_secret = payment_info.get("client_secret", "")
                
                if client_secret != "PENDING" and client_secret:
                    self.logger.info(f"Got valid client_secret on attempt {attempt}")
                    return client_secret
                
                if client_secret == "PENDING":
                    self.logger.warning(f"Client secret is 'PENDING' on attempt {attempt}/{max_attempts}")
                    
                    if attempt < max_attempts:
                        wait_time = 0.5 * (2 ** (attempt - 1))
                        self.logger.info(f"Waiting {wait_time:.1f}s before retry...")
                        await asyncio.sleep(wait_time)
                        continue
                
            except Exception as e:
                self.logger.warning(f"Failed to get payment info on attempt {attempt}: {str(e)}")
                if attempt < max_attempts:
                    await asyncio.sleep(1)
                    continue
        
        self.logger.warning(f"Could not get valid client_secret after {max_attempts} attempts, using empty string")
        return ""
    
    async def _is_duplicate_request(self, idempotency_key: str) -> bool:
        if not hasattr(self, '_processed_keys'):
            self._processed_keys = set()
        return idempotency_key in self._processed_keys

    async def _store_idempotency_key(self, idempotency_key: str):
        if not hasattr(self, '_processed_keys'):
            self._processed_keys = set()
        self._processed_keys.add(idempotency_key)
    
    @OrderServiceDecorators.handle_create_order_errors
    @trace_service_operation("create_order")
    async def create_order(self, request, order_data, user_id):
        with self.tracer.start_as_current_span("create-order-transaction") as span:
            span.set_attributes({
                "user_id": str(user_id),
                "item_count": len(order_data.items)
            })
            
            self.logger.info(f"Order creation attempt for user: {user_id}")
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

            items_hash = hashlib.md5(str(items_dict).encode()).hexdigest()[:8]
            idempotency_key = f"{user_id}_{items_hash}_{int(time.time())}"
            span.set_attribute("idempotency_key", idempotency_key)

            if self._circuit_open:
                raise Exception("Payment service unavailable (circuit breaker open)")

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
            self.logger.info(f"Order created successfully: {created_order.id}")
            span.set_attribute("order_id", str(created_order.id))

            try:
                payment = await self._create_payment(
                    order_id=str(created_order.id),
                    amount=created_order.total,
                    user_id=user_id,
                    payment_method_token=order_data.payment_method_token
                )
                payment_id = payment.payment_id
                await self.order_repo.update_order_payment_id(created_order.id, payment_id)
                await self.order_repo.update_order_status(created_order.id, OrderStatus.PENDING)
                created_order.client_secret = payment.client_secret
                created_order.payment_id = payment_id
                created_order.status = OrderStatus.PENDING
                
                order_response = self._build_order_response(created_order, items_dict)

                return order_response
                
            except Exception as payment_error:
                self.logger.error(f"Payment failed, rolling back order {created_order.id}: {payment_error}")
                
                try:
                    await self.order_repo.update_order_status(
                        created_order.id, 
                        OrderStatus.FAILED
                    )
                    self.logger.info(f"Order {created_order.id} successfully marked as FAILED")
                except Exception as rollback_error:
                    self.logger.error(f"Failed to rollback order {created_order.id}: {str(rollback_error)}")
                
                raise Exception(f"Order creation failed: Payment processing error. Order {created_order.id} marked as failed.")
    
    @OrderServiceDecorators.handle_get_order_errors
    @OrderServiceDecorators.validate_order_ownership
    @trace_service_operation("get_order")
    async def get_order(self, request, order_uuid, user_id, order_db):
        self.logger.info(f"Order retrieved successfully: {order_uuid}")

        order_response = self._build_order_response(order_db, order_db.items)
        order_response

        return order_response 

    @OrderServiceDecorators.handle_list_orders_errors
    @trace_service_operation("list_orders")
    async def list_orders(self, request, user_id, query_params):
        self.logger.info(f"Orders listing attempt for user: {user_id}")

        skip = (query_params.page - 1) * query_params.page_size

        all_orders_db = await self.order_repo.list_orders(skip=skip, limit=query_params.page_size)
        user_orders_db = [order for order in all_orders_db if order.user_id == user_id]
        user_total_count = len(user_orders_db)

        orders_with_items = []
        for order_db in user_orders_db:
            order_response = self._build_order_response(order_db, order_db.items)
            orders_with_items.append(order_response)

        order_list = pydantic_models.OrderList(
            items=orders_with_items,
            total=user_total_count,
            page=query_params.page,
            page_size=query_params.page_size
        )

        self.logger.info(f"Orders listed successfully for user: {user_id}")
        return order_list 
    
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
            "canceled": OrderStatus.CANCELED
        }
        
        order_status = status_mapping.get(status)
        if not order_status:
            raise Exception(f"Unknown status: {status}")
        
        if order.status == order_status:
            return {"status": "ignored", "reason": "already_in_state"}
        
        receipt_url = payment_data.get("receipt_url")
        await self.order_repo.update_order_status(order.id, order_status)
        await self.order_repo.update_order_receipt_url(order.id, receipt_url)
        
        if idempotency_key:
            await self._store_idempotency_key(idempotency_key)
        
        self.logger.info(f"Updated order {order_id} to {order_status.value}")
        
        return {"status": "success", "order_id": order_id, "updated_status": order_status.value}
        
    async def shutdown(self):
        await self.payment_client.close()