import logging
import os
from fastapi import APIRouter, Request, Depends, Query
from services.product_services import ProductService
from app.database import pydantic_models
from decorators.product_routes_decorators import ProductErrorDecorators

logger = logging.getLogger(__name__)

router = APIRouter(tags=['products'])

DEFAULT_PAGE_SIZE = int(os.getenv('DEFAULT_PAGE_SIZE', '20'))
MAX_PAGE_SIZE = int(os.getenv('MAX_PAGE_SIZE', '100'))

# Dependency injection functions
def get_product_service() -> ProductService:
    return ProductService(logger=logger)

@router.post(
    '/',
    response_model=pydantic_models.ProductResponse,
    status_code=201,
    summary="Create product"
)
@ProductErrorDecorators.handle_create_errors
async def create_product(
    request: Request,
    product_data: pydantic_models.ProductRequest,
    product_service: ProductService = Depends(get_product_service),
) -> pydantic_models.ProductResponse:
    return await product_service.create_product(request, product_data)

@router.get(
    '/',
    response_model=pydantic_models.ProductList,
    summary="List products (supports paging & filtering)"
)
@ProductErrorDecorators.handle_list_errors
async def list_products(
    request: Request,
    product_service: ProductService = Depends(get_product_service),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE, description="Page size"),
    q: str = Query(None, description="Search query"),
) -> pydantic_models.ProductList:
    query_params = pydantic_models.ProductQueryParams(
        page=page,
        page_size=page_size,
        q=q
    )
    return await product_service.list_products(request, query_params)

@router.get(
    '/{product_id}',
    response_model=pydantic_models.ProductResponse,
    summary="Get product details"
)
@ProductErrorDecorators.handle_get_errors
async def get_product(
    request: Request,
    product_id: str,
    product_service: ProductService = Depends(get_product_service),
) -> pydantic_models.ProductResponse:
    return await product_service.get_product(request, product_id)

@router.put(
    '/{product_id}',
    response_model=pydantic_models.ProductResponse,
    summary="Replace product (full update)"
)
@ProductErrorDecorators.handle_update_errors
async def update_product(
    request: Request,
    product_id: str,
    update_data: pydantic_models.ProductRequest,
    product_service: ProductService = Depends(get_product_service),
) -> pydantic_models.ProductResponse:
    return await product_service.update_product(request, product_id, update_data)

@router.patch(
    '/{product_id}',
    response_model=pydantic_models.ProductResponse,
    summary="Partially update product"
)
@ProductErrorDecorators.handle_patch_errors
async def patch_product(
    request: Request,
    product_id: str,
    patch_data: pydantic_models.ProductPatch,
    product_service: ProductService = Depends(get_product_service),
) -> pydantic_models.ProductResponse:
    return await product_service.patch_product(request, product_id, patch_data)

@router.delete(
    '/{product_id}',
    status_code=204,
    summary="Delete product"
)
@ProductErrorDecorators.handle_delete_errors
async def delete_product(
    request: Request,
    product_id: str,
    product_service: ProductService = Depends(get_product_service),
) -> None:
    return await product_service.delete_product(request, product_id)


@router.patch(
    '/{product_id}/inventory',
    response_model=pydantic_models.InventoryResponse,
    summary="Update product stock"
)
@ProductErrorDecorators.handle_inventory_errors
async def update_inventory(
    request: Request,
    product_id: str,
    inventory_data: pydantic_models.InventoryUpdate,
    product_service: ProductService = Depends(get_product_service),
):
    return await product_service.update_inventory(request, product_id, inventory_data)