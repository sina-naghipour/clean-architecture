from .order_helpers import create_problem_response
from fastapi import Request
from fastapi.responses import JSONResponse
from app.database import pydantic_models
from datetime import datetime

class OrderService:
    def __init__(self, logger):
        self.logger = logger
        self.orders = {}
        self.next_order_id = 1
        self.user_carts = {}

    async def create_order(
        self,
        request: Request,
        order_data: pydantic_models.OrderCreate,
        user_id: str,
    ):
        self.logger.info(f"Order creation attempt for user: {user_id}")
        
        cart = self.user_carts.get(user_id)
        if not cart or not cart.get('items'):
            return create_problem_response(
                status_code=400,
                error_type="bad-request",
                title="Bad Request",
                detail="Cannot create order with empty cart",
                instance=str(request.url)
            )
        
        order_id = f"order_{self.next_order_id}"
        total = sum(item['quantity'] * item['unit_price'] for item in cart['items'])
        
        order_items = [
            pydantic_models.OrderItemResponse(
                product_id=item['product_id'],
                name=item['name'],
                quantity=item['quantity'],
                unit_price=item['unit_price']
            ) for item in cart['items']
        ]
        
        order = pydantic_models.OrderResponse(
            id=order_id,
            status=pydantic_models.OrderStatus.CREATED,
            total=total,
            items=order_items,
            billing_address_id=order_data.billing_address_id,
            shipping_address_id=order_data.shipping_address_id,
            created_at=datetime.now().isoformat()
        )
        
        self.orders[order_id] = {
            'id': order_id,
            'user_id': user_id,
            'status': pydantic_models.OrderStatus.CREATED,
            'total': total,
            'items': cart['items'],
            'billing_address_id': order_data.billing_address_id,
            'shipping_address_id': order_data.shipping_address_id,
            'created_at': datetime.now().isoformat()
        }
        
        self.user_carts[user_id] = {'items': []}
        self.next_order_id += 1
        
        self.logger.info(f"Order created successfully: {order_id}")
        
        response = JSONResponse(
            status_code=201,
            content=order.model_dump(),
            headers={"Location": f"/api/orders/{order_id}"}
        )
        return response

    async def get_order(
        self,
        request: Request,
        order_id: str,
        user_id: str,
    ):
        self.logger.info(f"Order retrieval attempt: {order_id}")
        
        order_data = self.orders.get(order_id)
        
        if not order_data:
            return create_problem_response(
                status_code=404,
                error_type="not-found",
                title="Not Found",
                detail="Order not found",
                instance=str(request.url)
            )
        
        if order_data['user_id'] != user_id:
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
            ) for item in order_data['items']
        ]
        
        order = pydantic_models.OrderResponse(
            id=order_data['id'],
            status=order_data['status'],
            total=order_data['total'],
            items=order_items,
            billing_address_id=order_data['billing_address_id'],
            shipping_address_id=order_data['shipping_address_id'],
            created_at=order_data['created_at']
        )
        
        self.logger.info(f"Order retrieved successfully: {order_id}")
        return order

    async def list_orders(
        self,
        request: Request,
        user_id: str,
        query_params: pydantic_models.OrderQueryParams
    ):
        self.logger.info(f"Orders listing attempt for user: {user_id}")
        
        user_orders = [order for order in self.orders.values() if order['user_id'] == user_id]
        
        start_idx = (query_params.page - 1) * query_params.page_size
        end_idx = start_idx + query_params.page_size
        paginated_orders = user_orders[start_idx:end_idx]
        
        orders_with_items = []
        for order in paginated_orders:
            order_items = [
                pydantic_models.OrderItemResponse(
                    product_id=item['product_id'],
                    name=item['name'],
                    quantity=item['quantity'],
                    unit_price=item['unit_price']
                ) for item in order['items']
            ]
            
            order_response = pydantic_models.OrderResponse(
                id=order['id'],
                status=order['status'],
                total=order['total'],
                items=order_items,
                billing_address_id=order['billing_address_id'],
                shipping_address_id=order['shipping_address_id'],
                created_at=order['created_at']
            )
            orders_with_items.append(order_response)
        
        order_list = pydantic_models.OrderList(
            items=orders_with_items,
            total=len(user_orders),
            page=query_params.page,
            page_size=query_params.page_size
        )
        
        self.logger.info(f"Orders listed successfully for user: {user_id}")
        return order_list

    def _create_mock_cart(self, user_id: str):
        self.user_carts[user_id] = {
            'items': [
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
        }
