from .product_helpers import create_problem_response
from fastapi import Request
from fastapi.responses import JSONResponse
from database import pydantic_models
from repositories.product_repository import ProductRepository
from database.database_models import ProductDB
from datetime import datetime

class ProductService:
    def __init__(self, logger):
        self.logger = logger
        self.product_repository = ProductRepository()

    async def create_product(
        self,
        request: Request,
        product_data: pydantic_models.ProductRequest
    ):
        self.logger.info(f"Product creation attempt: {product_data.name}")
        
        product_db = ProductDB(
            name=product_data.name,
            price=product_data.price,
            stock=product_data.stock,
            description=product_data.description
        )
        
        created_product = await self.product_repository.create_product(product_db)
        
        if not created_product:
            return create_problem_response(
                status_code=409,
                error_type="conflict",
                title="Conflict",
                detail="Product with this name already exists",
                instance=str(request.url)
            )
        
        product_response = pydantic_models.ProductResponse(
            id=created_product.id,
            name=created_product.name,
            price=created_product.price,
            stock=created_product.stock,
            description=created_product.description
        )
        
        self.logger.info(f"Product created successfully: {created_product.id}")
        
        response = JSONResponse(
            status_code=201,
            content=product_response.model_dump(),
            headers={"Location": f"/api/products/{created_product.id}"}
        )
        return response

    async def get_product(
        self,
        request: Request,
        product_id: str
    ):
        self.logger.info(f"Product retrieval attempt: {product_id}")
        
        product_db = await self.product_repository.get_product_by_id(product_id)
        
        if not product_db:
            return create_problem_response(
                status_code=404,
                error_type="not-found",
                title="Not Found",
                detail="Product not found",
                instance=str(request.url)
            )
        
        product_response = pydantic_models.ProductResponse(
            id=product_db.id,
            name=product_db.name,
            price=product_db.price,
            stock=product_db.stock,
            description=product_db.description
        )
        
        self.logger.info(f"Product retrieved successfully: {product_id}")
        return product_response

    async def list_products(
        self,
        request: Request,
        query_params: pydantic_models.ProductQueryParams
    ):
        self.logger.info(f"Products listing attempt - Page: {query_params.page}, Size: {query_params.page_size}")
        
        skip = (query_params.page - 1) * query_params.page_size
        limit = query_params.page_size
        
        products_db = await self.product_repository.list_products(
            skip=skip,
            limit=limit,
            search_query=query_params.q
        )
        
        total = await self.product_repository.count_products(search_query=query_params.q)
        
        items = [
            pydantic_models.ProductResponse(
                id=product.id,
                name=product.name,
                price=product.price,
                stock=product.stock,
                description=product.description
            )
            for product in products_db
        ]
        
        product_list = pydantic_models.ProductList(
            items=items,
            total=total,
            page=query_params.page,
            page_size=query_params.page_size
        )
        
        self.logger.info(f"Products listed successfully - Found: {total}")
        return product_list

    async def update_product(
        self,
        request: Request,
        product_id: str,
        update_data: pydantic_models.ProductRequest
    ):
        self.logger.info(f"Product update attempt: {product_id}")
        
        update_dict = {
            "name": update_data.name,
            "price": update_data.price,
            "stock": update_data.stock,
            "description": update_data.description
        }
        
        updated_product_db = await self.product_repository.update_product(product_id, update_dict)
        
        if not updated_product_db:
            return create_problem_response(
                status_code=404,
                error_type="not-found",
                title="Not Found",
                detail="Product not found or name conflict",
                instance=str(request.url)
            )
        
        updated_product = pydantic_models.ProductResponse(
            id=updated_product_db.id,
            name=updated_product_db.name,
            price=updated_product_db.price,
            stock=updated_product_db.stock,
            description=updated_product_db.description
        )
        
        self.logger.info(f"Product updated successfully: {product_id}")
        return updated_product

    async def patch_product(
        self,
        request: Request,
        product_id: str,
        patch_data: pydantic_models.ProductPatch
    ):
        self.logger.info(f"Product patch attempt: {product_id}")
        
        patch_dict = patch_data.model_dump(exclude_unset=True)
        
        patched_product_db = await self.product_repository.patch_product(product_id, patch_dict)
        
        if not patched_product_db:
            return create_problem_response(
                status_code=404,
                error_type="not-found",
                title="Not Found",
                detail="Product not found or name conflict",
                instance=str(request.url)
            )
        
        patched_product = pydantic_models.ProductResponse(
            id=patched_product_db.id,
            name=patched_product_db.name,
            price=patched_product_db.price,
            stock=patched_product_db.stock,
            description=patched_product_db.description
        )
        
        self.logger.info(f"Product patched successfully: {product_id}")
        return patched_product

    async def delete_product(
        self,
        request: Request,
        product_id: str
    ):
        self.logger.info(f"Product deletion attempt: {product_id}")
        
        deleted = await self.product_repository.delete_product(product_id)
        
        if not deleted:
            return create_problem_response(
                status_code=404,
                error_type="not-found",
                title="Not Found",
                detail="Product not found",
                instance=str(request.url)
            )
        
        self.logger.info(f"Product deleted successfully: {product_id}")
        return None

    async def update_inventory(
        self,
        request: Request,
        product_id: str,
        inventory_data: pydantic_models.InventoryUpdate
    ):
        self.logger.info(f"Inventory update attempt: {product_id}")
        
        updated_product_db = await self.product_repository.update_inventory(
            product_id, 
            inventory_data.stock
        )
        
        if not updated_product_db:
            return create_problem_response(
                status_code=404,
                error_type="not-found",
                title="Not Found",
                detail="Product not found",
                instance=str(request.url)
            )
        
        response_data = pydantic_models.InventoryResponse(
            id=updated_product_db.id,
            stock=updated_product_db.stock
        )
        
        self.logger.info(f"Inventory updated successfully: {product_id} -> Stock: {inventory_data.stock}")
        return response_data