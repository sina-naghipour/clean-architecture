import logging
from functools import wraps
from typing import Callable, Any, TypeVar, Coroutine
from fastapi import HTTPException

logger = logging.getLogger(__name__)

F = TypeVar('F', bound=Callable[..., Any])
C = TypeVar('C', bound=Callable[..., Coroutine[Any, Any, Any]])


def handle_image_errors(func: C) -> C:
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Internal server error")
    return wrapper


def validate_product_exists(product_repo_attr: str = "product_repository"):
    def decorator(func: C) -> C:
        @wraps(func)
        async def wrapper(self, product_id: str, *args, **kwargs):
            product_repo = getattr(self, product_repo_attr)
            product = await product_repo.get_product_by_id(product_id)
            if not product:
                raise HTTPException(status_code=404, detail="Product not found")
            return await func(self, product_id, *args, **kwargs)
        return wrapper
    return decorator


def validate_image_exists(image_repo_attr: str = "image_repository"):
    def decorator(func: C) -> C:
        @wraps(func)
        async def wrapper(self, product_id: str, image_id: str, *args, **kwargs):
            image_repo = getattr(self, image_repo_attr)
            image = await image_repo.get_image_by_id(image_id)
            if not image or image.product_id != product_id:
                raise HTTPException(status_code=404, detail="Image not found")
            return await func(self, product_id, image_id, *args, **kwargs)
        return wrapper
    return decorator


def validate_file_size(max_size: int = 5 * 1024 * 1024):
    def decorator(func: C) -> C:
        @wraps(func)
        async def wrapper(self, product_id: str, upload_file, *args, **kwargs):
            file_content = await upload_file.read()
            await upload_file.seek(0)
            
            if len(file_content) > max_size:
                raise HTTPException(
                    status_code=413, 
                    detail=f"File size exceeds maximum allowed size of {max_size // 1024 // 1024}MB"
                )
            
            return await func(self, product_id, upload_file, *args, **kwargs)
        return wrapper
    return decorator


def validate_image_format(func: C) -> C:
    @wraps(func)
    async def wrapper(self, product_id: str, upload_file, *args, **kwargs):
        file_content = await upload_file.read()
        await upload_file.seek(0)
        
        if not self._validate_image_content(file_content):
            raise HTTPException(status_code=415, detail="Invalid image format")
        
        return await func(self, product_id, upload_file, *args, **kwargs)
    return wrapper


def validate_path_security(func: C) -> C:
    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        result = await func(self, *args, **kwargs)
        
        if hasattr(result, 'file_path'):
            if not self._validate_file_path(result.file_path):
                raise HTTPException(status_code=400, detail="Invalid file path")
        
        return result
    return wrapper


def transaction_with_rollback(func: C) -> C:
    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        try:
            return await func(self, *args, **kwargs)
        except Exception as e:
            if hasattr(self, 'image_repository'):
                await self.image_repository.rollback()
            if hasattr(self, 'product_repository'):
                await self.product_repository.rollback()
            raise
    return wrapper