from .product_helpers import create_problem_response
from fastapi import Request
from fastapi.responses import JSONResponse
from database import models
from datetime import datetime

class ProductService:
    def __init__(self, logger):
        self.logger = logger
        # Mock data storage
        self.products = {}
        self.next_id = 1

    async def create_product(
        self,
        request: Request,
        product_data: models.ProductRequest
    ):
        self.logger.info(f"Product creation attempt: {product_data.name}")
        
        for product in self.products.values():
            if product['name'].lower() == product_data.name.lower():
                return create_problem_response(
                    status_code=409,
                    error_type="conflict",
                    title="Conflict",
                    detail="Product with this name already exists",
                    instance=str(request.url)
                )
        
        # Create product
        product_id = f"prod_{self.next_id}"
        
        product = models.ProductResponse(
            id=product_id,
            name=product_data.name,
            price=product_data.price,
            stock=product_data.stock,
            description=product_data.description
        )
        
        # Store in mock database
        self.products[product_id] = {
            'id': product_id,
            'name': product_data.name,
            'price': product_data.price,
            'stock': product_data.stock,
            'description': product_data.description,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
        self.next_id += 1
        
        self.logger.info(f"Product created successfully: {product_id}")
        
        response = JSONResponse(
            status_code=201,
            content=product.model_dump(),
            headers={"Location": f"/api/products/{product_id}"}
        )
        return response

    async def get_product(
        self,
        request: Request,
        product_id: str
    ):
        self.logger.info(f"Product retrieval attempt: {product_id}")
        
        product_data = self.products.get(product_id)
        
        if not product_data:
            return create_problem_response(
                status_code=404,
                error_type="not-found",
                title="Not Found",
                detail="Product not found",
                instance=str(request.url)
            )
        
        product = models.ProductResponse(**product_data)
        
        self.logger.info(f"Product retrieved successfully: {product_id}")
        return product

    async def list_products(
        self,
        request: Request,
        query_params: models.ProductQueryParams
    ):
        self.logger.info(f"Products listing attempt - Page: {query_params.page}, Size: {query_params.page_size}")
        
        # Mock implementation
        all_products = list(self.products.values())
        
        if query_params.q:
            search_term = query_params.q.lower()
            all_products = [
                p for p in all_products 
                if search_term in p['name'].lower() or 
                   (p['description'] and search_term in p['description'].lower())
            ]
        
        start_idx = (query_params.page - 1) * query_params.page_size
        end_idx = start_idx + query_params.page_size
        paginated_products = all_products[start_idx:end_idx]
        
        items = [models.ProductResponse(**product) for product in paginated_products]
        
        product_list = models.ProductList(
            items=items,
            total=len(all_products),
            page=query_params.page,
            page_size=query_params.page_size
        )
        
        self.logger.info(f"Products listed successfully - Found: {len(all_products)}")
        return product_list

    async def update_product(
        self,
        request: Request,
        product_id: str,
        update_data: models.ProductRequest
    ):
        self.logger.info(f"Product update attempt: {product_id}")
        
        product_data = self.products.get(product_id)
        
        if not product_data:
            return create_problem_response(
                status_code=404,
                error_type="not-found",
                title="Not Found",
                detail="Product not found",
                instance=str(request.url)
            )
        
        for pid, product in self.products.items():
            if pid != product_id and product['name'].lower() == update_data.name.lower():
                return create_problem_response(
                    status_code=409,
                    error_type="conflict",
                    title="Conflict",
                    detail="Product with this name already exists",
                    instance=str(request.url)
                )
        
        # Update product
        updated_product = models.ProductResponse(
            id=product_id,
            name=update_data.name,
            price=update_data.price,
            stock=update_data.stock,
            description=update_data.description
        )
        
        self.products[product_id] = {
            **self.products[product_id],
            'name': update_data.name,
            'price': update_data.price,
            'stock': update_data.stock,
            'description': update_data.description,
            'updated_at': datetime.now()
        }
        
        self.logger.info(f"Product updated successfully: {product_id}")
        return updated_product

    async def patch_product(
        self,
        request: Request,
        product_id: str,
        patch_data: models.ProductPatch
    ):
        self.logger.info(f"Product patch attempt: {product_id}")
        
        product_data = self.products.get(product_id)
        
        if not product_data:
            return create_problem_response(
                status_code=404,
                error_type="not-found",
                title="Not Found",
                detail="Product not found",
                instance=str(request.url)
            )
        
        # Apply partial updates
        update_dict = patch_data.model_dump(exclude_unset=True)
        
        if 'name' in update_dict:
            for pid, product in self.products.items():
                if pid != product_id and product['name'].lower() == update_dict['name'].lower():
                    return create_problem_response(
                        status_code=409,
                        error_type="conflict",
                        title="Conflict",
                        detail="Product with this name already exists",
                        instance=str(request.url)
                    )
        
        # Merge updates with existing data
        merged_data = {**product_data, **update_dict, 'updated_at': datetime.now()}
        
        updated_product = models.ProductResponse(**merged_data)
        self.products[product_id] = merged_data
        
        self.logger.info(f"Product patched successfully: {product_id}")
        return updated_product

    async def delete_product(
        self,
        request: Request,
        product_id: str
    ):
        self.logger.info(f"Product deletion attempt: {product_id}")
        
        if product_id not in self.products:
            return create_problem_response(
                status_code=404,
                error_type="not-found",
                title="Not Found",
                detail="Product not found",
                instance=str(request.url)
            )
        
        del self.products[product_id]
        
        self.logger.info(f"Product deleted successfully: {product_id}")
        return None

    async def update_inventory(
        self,
        request: Request,
        product_id: str,
        inventory_data: models.InventoryUpdate
    ):
        self.logger.info(f"Inventory update attempt: {product_id}")
        
        product_data = self.products.get(product_id)
        
        if not product_data:
            return create_problem_response(
                status_code=404,
                error_type="not-found",
                title="Not Found",
                detail="Product not found",
                instance=str(request.url)
            )
        
        # Update stock
        self.products[product_id] = {
            **self.products[product_id],
            'stock': inventory_data.stock,
            'updated_at': datetime.now()
        }
        
        response_data = models.InventoryResponse(
            id=product_id,
            stock=inventory_data.stock
        )
        
        self.logger.info(f"Inventory updated successfully: {product_id} -> Stock: {inventory_data.stock}")
        return response_data