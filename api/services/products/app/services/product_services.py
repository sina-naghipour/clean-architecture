import os
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from .product_image_client import ProductImageClient

from .product_helpers import create_problem_response
from fastapi import Request, UploadFile
from fastapi.responses import JSONResponse
from database import pydantic_models
from repositories.product_repository import ProductRepository
from database.database_models import ProductDB
from datetime import datetime
from typing import List, Optional


def get_image_client() -> ProductImageClient:
    base_url = os.getenv(
        "STATIC_SERVICE_URL",
        "http://localhost:8005/api/static"
    )
    
    return ProductImageClient(
        base_url=base_url,
        timeout=float(os.getenv("IMAGE_CLIENT_TIMEOUT", "30.0")),
        max_concurrent=int(os.getenv("IMAGE_CLIENT_MAX_CONCURRENT", "10")),
        logger=logging.getLogger("product_image_client")
    )


@asynccontextmanager
async def image_client() -> AsyncGenerator[ProductImageClient, None]:
    client = get_image_client()
    try:
        yield client
    finally:
        await client.close()


class ProductService:
    def __init__(self, logger):
        self.logger = logger
        self.product_repository = ProductRepository()
        self.image_client = get_image_client()

    async def create_product(
        self,
        request: Request,
        product_data: pydantic_models.ProductRequest
    ) -> pydantic_models.ProductResponse:
        self.logger.info(f"Product creation attempt: {product_data.name}")
        
        product_db = ProductDB(
            name=product_data.name,
            price=product_data.price,
            stock=product_data.stock,
            description=product_data.description,
            tags=product_data.tags,
            images=product_data.images
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
            description=created_product.description,
            tags=created_product.tags,
            images=created_product.images,
            created_at=created_product.created_at,
            updated_at=created_product.updated_at
        )
        
        # Convert to dict and ensure datetime is serialized to ISO format
        response_content = product_response.model_dump()
        response_content["created_at"] = response_content["created_at"].isoformat()
        response_content["updated_at"] = response_content["updated_at"].isoformat()
        
        self.logger.info(f"Product created successfully: {created_product.id}")
        
        return product_response

    async def create_product_with_images(
        self,
        request: Request,
        product_data: pydantic_models.ProductRequest,
        image_files: List[UploadFile]
    ):
        self.logger.info(f"Product creation with images attempt: {product_data.name}")
        
        if image_files:
            self.logger.info(f"Uploading {len(image_files)} images...")
            results = await self.image_client.upload_images(
                image_files,
                subdirectory=f"products",
                metadata_list=[{"is_product_image": True} for _ in image_files]
            )
            
            image_urls = []
            for result in results:
                if result.success:
                    image_urls.append(result.url)
                    self.logger.info(f"Image uploaded: {result.url}")
                else:
                    self.logger.warning(f"Image upload failed: {result.error}")
            
            product_data.images = image_urls
        
        return await self.create_product(request, product_data)

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
        
        valid_images = []
        for image_url in product_db.images:
            if await self.image_client.validate_image(image_url):
                valid_images.append(image_url)
            else:
                self.logger.warning(f"Invalid image URL for product {product_id}: {image_url}")
        
        if len(valid_images) != len(product_db.images):
            await self.product_repository.update_product_images(product_id, valid_images)
            product_db.images = valid_images
        
        product_response = pydantic_models.ProductResponse(
            id=product_db.id,
            name=product_db.name,
            price=product_db.price,
            stock=product_db.stock,
            description=product_db.description,
            tags=product_db.tags,
            images=product_db.images,
            created_at=product_db.created_at,
            updated_at=product_db.updated_at
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
            search_query=query_params.q,
            tags=query_params.tags,
            min_price=query_params.min_price,
            max_price=query_params.max_price
        )
        
        total = await self.product_repository.count_products(
            search_query=query_params.q,
            tags=query_params.tags,
            min_price=query_params.min_price,
            max_price=query_params.max_price
        )
        
        items = [
            pydantic_models.ProductResponse(
                id=product.id,
                name=product.name,
                price=product.price,
                stock=product.stock,
                description=product.description,
                tags=product.tags,
                images=product.images,
                created_at=product.created_at,
                updated_at=product.updated_at
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
            "description": update_data.description,
            "tags": update_data.tags,
            "images": update_data.images
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
            description=updated_product_db.description,
            tags=updated_product_db.tags,
            images=updated_product_db.images,
            created_at=updated_product_db.created_at,
            updated_at=updated_product_db.updated_at
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
        
        patch_dict = patch_data.model_dump(exclude_unset=True, exclude_none=True)
        
        patched_product_db = await self.product_repository.update_product(product_id, patch_dict)
        
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
            description=patched_product_db.description,
            tags=patched_product_db.tags,
            images=patched_product_db.images,
            created_at=patched_product_db.created_at,
            updated_at=patched_product_db.updated_at
        )
        
        self.logger.info(f"Product patched successfully: {product_id}")
        return patched_product

    async def delete_product(
        self,
        request: Request,
        product_id: str
    ):
        self.logger.info(f"Product deletion attempt: {product_id}")
        
        product = await self.product_repository.get_product_by_id(product_id)
        if not product:
            return create_problem_response(
                status_code=404,
                error_type="not-found",
                title="Not Found",
                detail="Product not found",
                instance=str(request.url)
            )
        
        deleted_count = 0
        for image_url in product.images:
            file_id = self.image_client.extract_file_id(image_url)
            if file_id and await self.image_client.delete_image(file_id):
                deleted_count += 1
        
        if deleted_count > 0:
            self.logger.info(f"Deleted {deleted_count} images for product {product_id}")
        
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
    
    async def add_product_images(
        self,
        request: Request,
        product_id: str,
        image_files: List[UploadFile]
    ):
        self.logger.info(f"Adding images to product: {product_id}")
        
        product = await self.product_repository.get_product_by_id(product_id)
        if not product:
            return create_problem_response(
                status_code=404,
                error_type="not-found",
                title="Not Found",
                detail="Product not found",
                instance=str(request.url)
            )
        
        results = await self.image_client.upload_images(
            image_files,
            subdirectory=f"products/{product_id}",
            metadata_list=[{"product_id": product_id} for _ in image_files]
        )
        
        new_image_urls = []
        failed_count = 0
        for result in results:
            if result.success:
                new_image_urls.append(result.url)
                self.logger.info(f"Image uploaded for product {product_id}: {result.url}")
            else:
                failed_count += 1
                self.logger.error(f"Image upload failed: {result.error}")
        
        all_images = product.images + new_image_urls
        await self.product_repository.update_product_images(product_id, all_images)
        
        response_data = {
            "product_id": product_id,
            "added_count": len(new_image_urls),
            "failed_count": failed_count,
            "total_images": len(all_images),
            "new_images": new_image_urls
        }
        
        self.logger.info(f"Added {len(new_image_urls)} images to product {product_id}")
        return response_data

    async def remove_product_image(
        self,
        request: Request,
        product_id: str,
        image_url: str
    ):
        self.logger.info(f"Removing image from product: {product_id}")
        
        product = await self.product_repository.get_product_by_id(product_id)
        if not product:
            return create_problem_response(
                status_code=404,
                error_type="not-found",
                title="Not Found",
                detail="Product not found",
                instance=str(request.url)
            )
        
        if image_url not in product.images:
            return create_problem_response(
                status_code=404,
                error_type="not-found",
                title="Not Found",
                detail="Image not found in product",
                instance=str(request.url)
            )
        
        updated_images = [img for img in product.images if img != image_url]
        await self.product_repository.update_product_images(product_id, updated_images)
        
        file_id = self.image_client.extract_file_id(image_url)
        if file_id:
            await self.image_client.delete_image(file_id)
            self.logger.info(f"Deleted image file: {file_id}")
        
        response_data = {
            "product_id": product_id,
            "removed_image": image_url,
            "remaining_images": updated_images
        }
        
        self.logger.info(f"Removed image from product {product_id}")
        return response_data

    async def update_product_tags(
        self,
        request: Request,
        product_id: str,
        tag_data: pydantic_models.ProductTagUpdate
    ):
        self.logger.info(f"Updating tags for product: {product_id}")
        
        update_dict = {"tags": tag_data.tags}
        updated_product = await self.product_repository.update_product(product_id, update_dict)
        
        if not updated_product:
            return create_problem_response(
                status_code=404,
                error_type="not-found",
                title="Not Found",
                detail="Product not found",
                instance=str(request.url)
            )
        
        response_data = {
            "product_id": product_id,
            "updated_tags": updated_product.tags
        }
        
        self.logger.info(f"Updated tags for product {product_id}")
        return response_data

    async def cleanup_product_images(
        self,
        request: Request,
        product_id: str
    ):
        self.logger.info(f"Cleaning up images for product: {product_id}")
        
        product = await self.product_repository.get_product_by_id(product_id)
        if not product:
            return create_problem_response(
                status_code=404,
                error_type="not-found",
                title="Not Found",
                detail="Product not found",
                instance=str(request.url)
            )
        
        valid_images = []
        invalid_images = []
        
        for image_url in product.images:
            if await self.image_client.validate_image(image_url):
                valid_images.append(image_url)
            else:
                invalid_images.append(image_url)
        
        if invalid_images:
            await self.product_repository.update_product_images(product_id, valid_images)
            self.logger.info(f"Removed {len(invalid_images)} invalid images from product {product_id}")
        
        response_data = {
            "product_id": product_id,
            "valid_images": len(valid_images),
            "invalid_images_removed": len(invalid_images),
            "invalid_image_urls": invalid_images
        }
        
        return response_data

    async def close(self):
        await self.image_client.close()