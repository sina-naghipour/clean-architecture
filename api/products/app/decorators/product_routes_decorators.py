from functools import wraps
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

class ProductErrorDecorators:
    @staticmethod
    def handle_create_errors(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Create product error: {e}")
                raise HTTPException(status_code=500, detail="Internal server error")
        return wrapper

    @staticmethod
    def handle_list_errors(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"List products error: {e}")
                raise HTTPException(status_code=500, detail="Internal server error")
        return wrapper

    @staticmethod
    def handle_get_errors(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Get product error: {e}")
                raise HTTPException(status_code=500, detail="Internal server error")
        return wrapper

    @staticmethod
    def handle_update_errors(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Update product error: {e}")
                raise HTTPException(status_code=500, detail="Internal server error")
        return wrapper

    @staticmethod
    def handle_patch_errors(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Patch product error: {e}")
                raise HTTPException(status_code=500, detail="Internal server error")
        return wrapper

    @staticmethod
    def handle_delete_errors(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Delete product error: {e}")
                raise HTTPException(status_code=500, detail="Internal server error")
        return wrapper

    @staticmethod
    def handle_inventory_errors(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Update inventory error: {e}")
                raise HTTPException(status_code=500, detail="Internal server error")
        return wrapper