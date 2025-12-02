from functools import wraps
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

class ImageErrorDecorators:
    @staticmethod
    def handle_upload_errors(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except HTTPException as he:
                # Add 404 to the list of status codes that should be passed through
                if he.status_code in [400, 404, 413, 415]:
                    raise
                logger.error(f"Upload error: {he}")
                raise HTTPException(status_code=500, detail="Internal server error")
            except Exception as e:
                logger.error(f"Upload exception: {e}")
                raise HTTPException(status_code=500, detail="Internal server error")
        return wrapper

    @staticmethod
    def handle_batch_upload_errors(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except HTTPException as he:
                if he.status_code in [400, 404, 413, 415]:
                    raise
                
                if he.status_code == 207:
                    raise
                
                logger.error(f"Batch upload HTTP error: {he}")
                raise HTTPException(
                    status_code=500, 
                    detail="Internal server error during batch upload"
                )
            except ValueError as ve:
                logger.error(f"Batch upload validation error: {ve}")
                raise HTTPException(status_code=400, detail=str(ve))
            except Exception as e:
                logger.error(f"Batch upload unexpected error: {e}")
                raise HTTPException(
                    status_code=500,
                    detail="Failed to process batch upload request"
                )
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
                logger.error(f"List images error: {e}")
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
                logger.error(f"Get image error: {e}")
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
                logger.error(f"Delete image error: {e}")
                raise HTTPException(status_code=500, detail="Internal server error")
        return wrapper

    @staticmethod
    def handle_primary_errors(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Set primary image error: {e}")
                raise HTTPException(status_code=500, detail="Internal server error")
        return wrapper