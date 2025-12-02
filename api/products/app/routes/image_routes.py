import logging
import os
from fastapi import APIRouter, Request, Depends, UploadFile, File, Form
from services.image_services import ImageService
from database import pydantic_models
from typing import List
from decorators.image_routes_decorators import ImageErrorDecorators

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/images", tags=['Product Images'])

def get_image_service() -> ImageService:
    return ImageService()

@router.post(
    '/products/{product_id}',
    response_model=pydantic_models.ProductImage,
    status_code=201,
    summary="Upload product image"
)
@ImageErrorDecorators.handle_upload_errors
async def upload_product_image(
    request: Request,
    product_id: str,
    file: UploadFile = File(...),
    is_primary: bool = Form(False),
    image_service: ImageService = Depends(get_image_service),
) -> pydantic_models.ProductImage:
    return await image_service.upload_product_image(
        product_id=product_id,
        upload_file=file,
        is_primary=is_primary
    )

@router.post(
    '/products/{product_id}/batch',
    response_model=pydantic_models.ProductImageBatchResponse,
    status_code=207,
    summary="Upload multiple product images"
)
@ImageErrorDecorators.handle_batch_upload_errors
async def upload_product_images_batch(
    request: Request,
    product_id: str,
    files: List[UploadFile] = File(...),
    make_primary_first: bool = Form(False),
    image_service: ImageService = Depends(get_image_service),
) -> pydantic_models.ProductImageBatchResponse:
    return await image_service.upload_product_images_batch(
        product_id=product_id,
        upload_files=files,
        make_primary_first=make_primary_first
    )

@router.get(
    '/products/{product_id}',
    response_model=pydantic_models.ProductImageList,
    summary="List product images"
)
@ImageErrorDecorators.handle_list_errors
async def list_product_images(
    request: Request,
    product_id: str,
    image_service: ImageService = Depends(get_image_service),
) -> pydantic_models.ProductImageList:
    images = await image_service.get_product_images(product_id)
    
    return pydantic_models.ProductImageList(
        items=images,
        total=len(images)
    )

@router.get(
    '/products/{product_id}/{image_id}',
    response_model=pydantic_models.ProductImage,
    summary="Get product image metadata"
)
@ImageErrorDecorators.handle_get_errors
async def get_product_image(
    request: Request,
    product_id: str,
    image_id: str,
    image_service: ImageService = Depends(get_image_service),
) -> pydantic_models.ProductImage:
    images = await image_service.get_product_images(product_id)
    
    for image in images:
        if image.id == image_id:
            return image
    
    from services.product_helpers import create_problem_response
    return create_problem_response(
        status_code=404,
        error_type="not-found",
        title="Not Found",
        detail="Image not found",
        instance=str(request.url)
    )

@router.delete(
    '/products/{product_id}/{image_id}',
    status_code=204,
    summary="Delete product image"
)
@ImageErrorDecorators.handle_delete_errors
async def delete_product_image(
    request: Request,
    product_id: str,
    image_id: str,
    image_service: ImageService = Depends(get_image_service),
) -> None:
    deleted = await image_service.delete_product_image(product_id, image_id)
    
    if not deleted:
        from services.product_helpers import create_problem_response
        return create_problem_response(
            status_code=404,
            error_type="not-found",
            title="Not Found",
            detail="Image not found",
            instance=str(request.url)
        )
    
    return None

@router.patch(
    '/products/{product_id}/{image_id}/primary',
    response_model=pydantic_models.ProductImage,
    summary="Set image as primary for product"
)
@ImageErrorDecorators.handle_primary_errors
async def set_primary_image(
    request: Request,
    product_id: str,
    image_id: str,
    image_service: ImageService = Depends(get_image_service),
) -> pydantic_models.ProductImage:
    return await image_service.set_primary_image(product_id, image_id)