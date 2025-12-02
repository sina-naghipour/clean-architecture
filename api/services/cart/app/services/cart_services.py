from .cart_helpers import create_problem_response
from fastapi import Request
from fastapi.responses import JSONResponse
from database import models
from datetime import datetime

class CartService:
    def __init__(self, logger):
        self.logger = logger
        # Mock data storage
        self.carts = {}
        self.next_cart_id = 1
        self.next_item_id = 1
        # Mock product data for demonstration
        self.products = {
            "prod_1": {"name": "Laptop", "price": 999.99},
            "prod_2": {"name": "Mouse", "price": 29.99},
            "prod_3": {"name": "Keyboard", "price": 79.99}
        }

    async def get_cart(
        self,
        request: Request,
        user_id: str
    ):
        self.logger.info(f"Cart retrieval attempt for user: {user_id}")
        
        cart_data = self.carts.get(user_id)
        
        if not cart_data:
            return create_problem_response(
                status_code=404,
                error_type="not-found",
                title="Not Found",
                detail="Cart not found",
                instance=str(request.url)
            )
        
        total = sum(item['quantity'] * item['unit_price'] for item in cart_data['items'])
        
        cart_response = models.CartResponse(
            id=cart_data['id'],
            user_id=cart_data['user_id'],
            items=[models.CartItemResponse(**item) for item in cart_data['items']],
            total=total
        )
        
        self.logger.info(f"Cart retrieved successfully for user: {user_id}")
        return cart_response

    async def add_cart_item(
        self,
        request: Request,
        user_id: str,
        item_data: models.CartItemRequest
    ):
        self.logger.info(f"Add item attempt for user: {user_id}, product: {item_data.product_id}")

        product = self.products.get(item_data.product_id)
        if not product:
            return create_problem_response(
                status_code=404,
                error_type="not-found",
                title="Not Found",
                detail="Product not found",
                instance=str(request.url)
            )
        
        if user_id not in self.carts:
            cart_id = f"cart_{self.next_cart_id}"
            self.carts[user_id] = {
                'id': cart_id,
                'user_id': user_id,
                'items': [],
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }
            self.next_cart_id += 1
        
        cart_data = self.carts[user_id]
        
        existing_item = None
        for item in cart_data['items']:
            if item['product_id'] == item_data.product_id:
                existing_item = item
                break
        
        if existing_item:
            # Update quantity if item exists
            existing_item['quantity'] += item_data.quantity
            existing_item['updated_at'] = datetime.now()
            item_id = existing_item['id']
        else:
            # Add new item
            item_id = f"item_{self.next_item_id}"
            new_item = {
                'id': item_id,
                'product_id': item_data.product_id,
                'name': product['name'],
                'quantity': item_data.quantity,
                'unit_price': product['price'],
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }
            cart_data['items'].append(new_item)
            self.next_item_id += 1
        
        cart_data['updated_at'] = datetime.now()
        
        # Find the added/updated item for response
        response_item = None
        for item in cart_data['items']:
            if item['product_id'] == item_data.product_id:
                response_item = models.CartItemResponse(**item)
                break
        
        self.logger.info(f"Item added successfully to cart: {item_id}")
        
        response = JSONResponse(
            status_code=201,
            content=response_item.model_dump(),
            headers={"Location": f"/api/cart/items/{item_id}"}
        )
        return response

    async def update_cart_item(
        self,
        request: Request,
        user_id: str,
        item_id: str,
        update_data: models.CartItemUpdate
    ):
        self.logger.info(f"Update item attempt for user: {user_id}, item: {item_id}")
        
        cart_data = self.carts.get(user_id)
        
        if not cart_data:
            return create_problem_response(
                status_code=404,
                error_type="not-found",
                title="Not Found",
                detail="Cart not found",
                instance=str(request.url)
            )
        
        # Find the item
        target_item = None
        for item in cart_data['items']:
            if item['id'] == item_id:
                target_item = item
                break
        
        if not target_item:
            return create_problem_response(
                status_code=404,
                error_type="not-found",
                title="Not Found",
                detail="Cart item not found",
                instance=str(request.url)
            )
        
        # Update quantity
        target_item['quantity'] = update_data.quantity
        target_item['updated_at'] = datetime.now()
        cart_data['updated_at'] = datetime.now()
        
        response_item = models.CartItemResponse(**target_item)
        
        self.logger.info(f"Item updated successfully: {item_id}")
        return response_item

    async def remove_cart_item(
        self,
        request: Request,
        user_id: str,
        item_id: str
    ):
        self.logger.info(f"Remove item attempt for user: {user_id}, item: {item_id}")
        
        cart_data = self.carts.get(user_id)
        
        if not cart_data:
            return create_problem_response(
                status_code=404,
                error_type="not-found",
                title="Not Found",
                detail="Cart not found",
                instance=str(request.url)
            )
        
        # Find and remove the item
        item_found = False
        for i, item in enumerate(cart_data['items']):
            if item['id'] == item_id:
                cart_data['items'].pop(i)
                item_found = True
                break
        
        if not item_found:
            return create_problem_response(
                status_code=404,
                error_type="not-found",
                title="Not Found",
                detail="Cart item not found",
                instance=str(request.url)
            )
        
        cart_data['updated_at'] = datetime.now()
        
        self.logger.info(f"Item removed successfully: {item_id}")
        return None

    async def clear_cart(
        self,
        request: Request,
        user_id: str
    ):
        self.logger.info(f"Clear cart attempt for user: {user_id}")
        
        cart_data = self.carts.get(user_id)
        
        if not cart_data:
            return create_problem_response(
                status_code=404,
                error_type="not-found",
                title="Not Found",
                detail="Cart not found",
                instance=str(request.url)
            )
        
        # Clear all items
        cart_data['items'] = []
        cart_data['updated_at'] = datetime.now()
        
        self.logger.info(f"Cart cleared successfully for user: {user_id}")
        return None

    async def list_carts(
        self,
        request: Request,
        query_params: models.CartQueryParams
    ):
        self.logger.info(f"Carts listing attempt - Page: {query_params.page}, Size: {query_params.page_size}")
        
        # Convert carts dict to list
        all_carts = list(self.carts.values())
        
        start_idx = (query_params.page - 1) * query_params.page_size
        end_idx = start_idx + query_params.page_size
        paginated_carts = all_carts[start_idx:end_idx]
        
        # Calculate totals for each cart
        carts_with_totals = []
        for cart in paginated_carts:
            total = sum(item['quantity'] * item['unit_price'] for item in cart['items'])
            cart_response = models.CartResponse(
                id=cart['id'],
                user_id=cart['user_id'],
                items=[models.CartItemResponse(**item) for item in cart['items']],
                total=total
            )
            carts_with_totals.append(cart_response)
        
        cart_list = models.CartList(
            items=carts_with_totals,
            total=len(all_carts),
            page=query_params.page,
            page_size=query_params.page_size
        )
        
        self.logger.info(f"Carts listed successfully - Found: {len(all_carts)}")
        return cart_list
