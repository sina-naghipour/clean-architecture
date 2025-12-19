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

class OrderService:
    def __init__(self, logger, db_session):
        self.logger = logger
        self.order_repo = OrderRepository(db_session)
        self.payment_client = PaymentGRPCClient()

    async def _create_payment(self, order_id, amount, user_id, payment_method_token):
        try:
            payment = await self.payment_client.create_payment(
                order_id=order_id,
                amount=amount,
                user_id=user_id,
                payment_method_token=payment_method_token
            )
            return payment
        except grpc.RpcError as e:
            self.logger.error(f"Payment creation failed: {e.code().name} - {e.details()}")
            raise Exception(f"Payment processing failed: {e.details()}")
        except Exception as e:
            self.logger.error(f"Payment creation failed: {e}")
            raise Exception(f"Payment processing failed: {str(e)}")

    def _build_order_response(self, order_db, items_dict):
        order_items = [
            pydantic_models.OrderItemResponse(
                product_id=item['product_id'],
                name=item['name'],
                quantity=item['quantity'],
                unit_price=item['unit_price']
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
            created_at=created_at.isoformat()
        )


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
    

    @OrderServiceDecorators.handle_create_order_errors
    async def create_order(self, request, order_data, user_id):
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

        payment = await self._create_payment(
            order_id=str(created_order.id),
            amount=created_order.total,
            user_id=user_id,
            payment_method_token=order_data.payment_method_token
        )
        payment_id = payment.payment_id
             
        await self.order_repo.update_order_payment_id(created_order.id, payment_id)
        await self.order_repo.update_order_status(created_order.id, OrderStatus.PENDING)

        created_order.payment_id = payment_id
        created_order.status = OrderStatus.PENDING

        client_secret = payment.client_secret
        
        order_response = self._build_order_response(created_order, items_dict)
        order_response.client_secret = client_secret

        return order_response

    @OrderServiceDecorators.handle_get_order_errors
    @OrderServiceDecorators.validate_order_ownership
    async def get_order(self, request, order_uuid, user_id, order_db):
        self.logger.info(f"Order retrieved successfully: {order_uuid}")

        client_secret = ""
        if order_db.payment_id:
            try:
                payment_info = await self.payment_client.get_payment(order_db.payment_id)
                client_secret = payment_info.get("client_secret", "")
            except:
                pass

        order_response = self._build_order_response(order_db, order_db.items)
        order_response.client_secret = client_secret

        return order_response 

    @OrderServiceDecorators.handle_list_orders_errors
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
    async def handle_payment_webhook(self, request, payment_data: dict):
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
        receipt_url = payment_data.get("receipt_url")
        await self.order_repo.update_order_status(order.id, order_status)
        await self.order_repo.update_order_receipt_url(order.id, receipt_url)
        self.logger.info(f"Updated order {order_id} to {order_status.value}")
        
        return {"status": "success", "order_id": order_id, "updated_status": order_status.value}
    
    async def shutdown(self):
        await self.payment_client.close()
