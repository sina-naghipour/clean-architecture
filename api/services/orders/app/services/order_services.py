from .order_helpers import create_problem_response
from fastapi import Request
from fastapi.responses import JSONResponse
from database import pydantic_models
from datetime import datetime
from uuid import UUID
from repository.orders_repository import OrderRepository
from database.database_models import OrderDB, OrderStatus

class OrderService:
    def __init__(self, logger, db_session):
        self.logger = logger
        self.order_repo = OrderRepository(db_session)

    async def create_order(
        self,
        request: Request,
        order_data: pydantic_models.OrderCreate,
        user_id: str,
    ):
        self.logger.info(f"Order creation attempt for user: {user_id}")
        
        cart_items = [
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
        
        if not cart_items:
            return create_problem_response(
                status_code=400,
                error_type="bad-request",
                title="Bad Request",
                detail="Cannot create order with empty cart",
                instance=str(request.url)
            )
        
        total = sum(item['quantity'] * item['unit_price'] for item in cart_items)
        
        order_db = OrderDB(
            user_id=user_id,
            status=OrderStatus.CREATED,
            total=total,
            billing_address_id=order_data.billing_address_id,
            shipping_address_id=order_data.shipping_address_id,
            payment_method_token=order_data.payment_method_token,
            items=cart_items
        )
        
        try:
            created_order = await self.order_repo.create_order(order_db)
            self.logger.info(f"Order created successfully: {created_order.id}")
        except Exception as e:
            self.logger.error(f"Failed to create order: {e}")
            return create_problem_response(
                status_code=500,
                error_type="internal-error",
                title="Internal Server Error", 
                detail="Failed to create order",
                instance=str(request.url)
            )
        
        order_items = [
            pydantic_models.OrderItemResponse(
                product_id=item['product_id'],
                name=item['name'],
                quantity=item['quantity'],
                unit_price=item['unit_price']
            ) for item in cart_items
        ]
        
        created_at = created_order.created_at if created_order.created_at else datetime.utcnow()
        
        order_response = pydantic_models.OrderResponse(
            id=str(created_order.id),
            status=created_order.status,
            total=created_order.total,
            items=order_items,
            billing_address_id=created_order.billing_address_id,
            shipping_address_id=created_order.shipping_address_id,
            created_at=created_at.isoformat()
        )
        
        return JSONResponse(
            status_code=201,
            content=order_response.model_dump(),
            headers={"Location": f"/api/orders/{created_order.id}"}
        )

    async def get_order(
        self,
        request: Request,
        order_id: str,
        user_id: str,
    ):
        self.logger.info(f"Order retrieval attempt: {order_id}")
        try:
            order_uuid = UUID(order_id)
        except ValueError:
            return create_problem_response(
                status_code=400,
                error_type="bad-request",
                title="Bad Request",
                detail="Invalid order ID format",
                instance=str(request.url)
            )
        
        try:
            order_db = await self.order_repo.get_order_by_id(order_uuid)
        except Exception as e:
            self.logger.error(f"Failed to fetch order: {e}")
            return create_problem_response(
                status_code=500,
                error_type="internal-error",
                title="Internal Server Error",
                detail="Failed to fetch order",
                instance=str(request.url)
            )
        
        if not order_db:
            return create_problem_response(
                status_code=404,
                error_type="not-found",
                title="Not Found",
                detail="Order not found",
                instance=str(request.url)
            )
        
        if order_db.user_id != user_id:
            return create_problem_response(
                status_code=404,
                error_type="not-found",
                title="Not Found",
                detail="Order not found",
                instance=str(request.url)
            )
        
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
            created_at=created_at.isoformat()
        )
        
        self.logger.info(f"Order retrieved successfully: {order_id}")
        return order_response

    async def list_orders(
        self,
        request: Request,
        user_id: str,
        query_params: pydantic_models.OrderQueryParams
    ):
        self.logger.info(f"Orders listing attempt for user: {user_id}")
        
        skip = (query_params.page - 1) * query_params.page_size
        
        try:
            all_orders_db = await self.order_repo.list_orders(skip=skip, limit=query_params.page_size)
            user_orders_db = [order for order in all_orders_db if order.user_id == user_id]
            user_total_count = len(user_orders_db)
        except Exception as e:
            self.logger.error(f"Failed to list orders: {e}")
            return create_problem_response(
                status_code=500,
                error_type="internal-error",
                title="Internal Server Error",
                detail="Failed to list orders",
                instance=str(request.url)
            )
        
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