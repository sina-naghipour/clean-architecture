from functools import wraps
from typing import Callable, Any
from fastapi import HTTPException
from pathlib import Path


def handle_upload_errors(func: Callable) -> Callable:
    """Decorator to handle errors for upload operations."""
    @wraps(func)
    async def wrapper(self, upload_file, *args, **kwargs):
        try:
            return await func(self, upload_file, *args, **kwargs)
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))
        except PermissionError as e:
            raise HTTPException(status_code=403, detail=f"Permission denied: {str(e)}")
        except OSError as e:
            raise HTTPException(status_code=500, detail=f"File system error: {str(e)}")
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Upload operation failed: {str(e)}")
    return wrapper


def handle_delete_errors(func: Callable) -> Callable:
    """Decorator to handle errors for delete operations."""
    @wraps(func)
    async def wrapper(self, file_id, *args, **kwargs):
        try:
            return await func(self, file_id, *args, **kwargs)
        except HTTPException as he:
            if he.status_code == 404:
                return False
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Delete operation failed: {str(e)}")
    return wrapper


def handle_get_errors(func: Callable) -> Callable:
    """Decorator to handle errors for get operations."""
    @wraps(func)
    def wrapper(self, file_id, *args, **kwargs):
        try:
            return func(self, file_id, *args, **kwargs)
        except HTTPException:
            raise
        except KeyError as e:
            raise HTTPException(status_code=404, detail=f"File metadata not found: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Get operation failed: {str(e)}")
    return wrapper


def validate_path_security(func: Callable) -> Callable:
    """Decorator to validate path security before operations."""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if hasattr(self, 'upload_dir'):
            upload_dir = Path(self.upload_dir).resolve()
            
            if not upload_dir.exists():
                upload_dir.mkdir(parents=True, exist_ok=True)
            
            if not upload_dir.is_dir():
                raise HTTPException(
                    status_code=500, 
                    detail=f"Upload directory is not a valid directory: {upload_dir}"
                )
        
        return func(self, *args, **kwargs)
    return wrapper