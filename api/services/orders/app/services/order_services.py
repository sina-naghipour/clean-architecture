from .order_helpers import create_problem_response
from fastapi import Request
from fastapi.responses import JSONResponse
from database import pydantic_models
from datetime import datetime
from uuid import UUID
from repositories.orders_repository import OrderRepository
from database.database_models import OrderDB, OrderStatus
from decorators.order_services_decorators import OrderServiceDecorators
import httpx
import os

class OrderService:
    def __init__(self, logger, db_session):
        self.logger = logger
        self.order_repo = OrderRepository(db_session)
        self.payments_service_url = os.getenv("PAYMENTS_SERVICE_URL", "http://localhost:8004")
    
    async def _create_payment(self, order_id: str, amount: float, user_id: str, payment_method_token: str) -> str:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                payload = {
                    "order_id": order_id,
                    "amount": amount,
                    "user_id": user_id,
                    "payment_method_token": payment_method_token
                }
                response = await client.post(
                    f"{self.payments_service_url}/payments/",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                payment_data = response.json()
                return payment_data["id"]
        except Exception as e:
            self.logger.error(f"Payment creation failed: {e}")
            raise Exception(f"Payment processing failed: {str(e)}")
    
    async def _get_cart_items(self, user_id: str) -> list:
        return [
            {
                'product_id': 'prod_1',
                'name': 'Laptop', 
                'quantity': 1,
                'unit_price': 999.99
            },
            {
                'product_id': 'prod_2',
                'name': 'Mouse',
                'quantity': 2, 
                'unit_price': 29.99
            }
        ]
    
    @OrderServiceDecorators.handle_create_order_errors
    async def create_order(
        self,
        request: Request,
        order_data: pydantic_models.OrderCreate,
        user_id: str,
    ):
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
        
        try:
            payment_id = await self._create_payment(
                order_id=str(created_order.id),
                amount=created_order.total,
                user_id=user_id,
                payment_method_token=order_data.payment_method_token
            )
            
            await self.order_repo.update_order_payment_id(created_order.id, payment_id)
            await self.order_repo.update_order_status(created_order.id, OrderStatus.PAID)
            
            created_order.payment_id = payment_id
            created_order.status = OrderStatus.PAID
            
        except Exception as e:
            self.logger.error(f"Payment processing failed, keeping order as CREATED: {e}")
        
        order_items = [
            pydantic_models.OrderItemResponse(
                product_id=item['product_id'],
                name=item['name'],
                quantity=item['quantity'],
                unit_price=item['unit_price']
            ) for item in items_dict
        ]
        
        created_at = created_order.created_at if created_order.created_at else datetime.utcnow()
        
        order_response = pydantic_models.OrderResponse(
            id=str(created_order.id),
            status=created_order.status,
            total=created_order.total,
            items=order_items,
            billing_address_id=created_order.billing_address_id,
            shipping_address_id=created_order.shipping_address_id,
            payment_id=created_order.payment_id,
            created_at=created_at.isoformat()
        )
        
        return JSONResponse(
            status_code=201,
            content=order_response.model_dump(),
            headers={"Location": f"/api/orders/{created_order.id}"}
        )
    
    @OrderServiceDecorators.handle_get_order_errors
    @OrderServiceDecorators.validate_order_ownership
    async def get_order(
        self,
        request: Request,
        order_uuid: UUID,
        user_id: str,
        order_db: OrderDB,
    ):
        self.logger.info(f"Order retrieved successfully: {order_uuid}")
        
        order_items = [
            pydantic_models.OrderItemResponse(
                product_id=item['product_id'],
                name=item['name'],
                quantity=item['quantity'],
                unit_price=item['unit_price']
            ) for item in order_db.items
        ]
        
        created_at = order_db.created_at if order_db.created_at else datetime.utcnow()
        
        order_response = pydantic_models.OrderResponse(
            id=str(order_db.id),
            status=order_db.status,
            total=order_db.total,
            items=order_items,
            billing_address_id=order_db.billing_address_id,
            shipping_address_id=order_db.shipping_address_id,
            payment_id=order_db.payment_id,
            created_at=created_at.isoformat()
        )
        
        return order_response
    
    @OrderServiceDecorators.handle_list_orders_errors
    async def list_orders(
        self,
        request: Request,
        user_id: str,
        query_params: pydantic_models.OrderQueryParams
    ):
        self.logger.info(f"Orders listing attempt for user: {user_id}")
        
        skip = (query_params.page - 1) * query_params.page_size
        
        all_orders_db = await self.order_repo.list_orders(skip=skip, limit=query_params.page_size)
        user_orders_db = [order for order in all_orders_db if order.user_id == user_id]
        user_total_count = len(user_orders_db)
        
        orders_with_items = []
        for order_db in user_orders_db:
            order_items = [
                pydantic_models.OrderItemResponse(
                    product_id=item['product_id'],
                    name=item['name'],
                    quantity=item['quantity'],
                    unit_price=item['unit_price']
                ) for item in order_db.items
            ]
            
            created_at = order_db.created_at if order_db.created_at else datetime.utcnow()
            
            order_response = pydantic_models.OrderResponse(
                id=str(order_db.id),
                status=order_db.status,
                total=order_db.total,
                items=order_items,
                billing_address_id=order_db.billing_address_id,
                shipping_address_id=order_db.shipping_address_id,
                payment_id=order_db.payment_id,
                created_at=created_at.isoformat()
            )
            orders_with_items.append(order_response)
        
        order_list = pydantic_models.OrderList(
            items=orders_with_items,
            total=user_total_count,
            page=query_params.page,
            page_size=query_params.page_size
        )
        
        self.logger.info(f"Orders listed successfully for user: {user_id}")
        return order_list