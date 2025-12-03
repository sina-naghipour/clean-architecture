from functools import wraps
from typing import Callable, Any
from fastapi import HTTPException
import traceback


def handle_validation_errors(func: Callable) -> Callable:
    """
    Generic decorator for validation methods.
    Preserves existing HTTPExceptions, catches others and converts to appropriate errors.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except HTTPException:
            # Re-raise HTTPExceptions as-is
            raise
        except Exception as e:
            # Log unexpected errors
            error_detail = f"Validation failed: {str(e)}"
            raise HTTPException(
                status_code=500,
                detail=error_detail
            )
    return wrapper


def with_size_validation(func: Callable) -> Callable:
    """
    Specialized decorator for file size validation.
    Ensures 413 status code for file too large errors.
    """
    @wraps(func)
    def wrapper(self, file_content: bytes, *args, **kwargs):
        try:
            return func(self, file_content, *args, **kwargs)
        except HTTPException as he:
            # Ensure size validation errors are 413
            if "size" in he.detail.lower() or "maximum" in he.detail.lower():
                raise HTTPException(
                    status_code=413,
                    detail=he.detail
                ) from he
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Size validation error: {str(e)}"
            )
    return wrapper


def with_type_validation(func: Callable) -> Callable:
    """
    Specialized decorator for file type validation.
    Ensures 415 status code for unsupported media types.
    """
    @wraps(func)
    def wrapper(self, file_content: bytes, *args, **kwargs):
        try:
            return func(self, file_content, *args, **kwargs)
        except HTTPException as he:
            # Ensure type validation errors are 415
            if "type" in he.detail.lower() or "invalid" in he.detail.lower():
                raise HTTPException(
                    status_code=415,
                    detail=he.detail
                ) from he
            raise
        except Exception as e:
            raise HTTPException(
                status_code=415,
                detail=f"File type validation error: {str(e)}"
            )
    return wrapper


def with_filename_validation(func: Callable) -> Callable:
    """
    Specialized decorator for filename validation.
    Ensures 422 status code for validation errors.
    """
    @wraps(func)
    def wrapper(self, filename: str, *args, **kwargs):
        try:
            return func(self, filename, *args, **kwargs)
        except HTTPException as he:
            # Ensure filename validation errors are 422
            if he.status_code == 400:
                raise HTTPException(
                    status_code=422,  # Change 400 to 422 for validation
                    detail=he.detail
                ) from he
            raise
        except Exception as e:
            raise HTTPException(
                status_code=422,
                detail=f"Filename validation error: {str(e)}"
            )
    return wrapper


def validate_input_not_none(func: Callable) -> Callable:
    """
    Decorator to ensure input is not None before validation.
    """
    @wraps(func)
    def wrapper(self, input_data, *args, **kwargs):
        if input_data is None:
            raise HTTPException(
                status_code=422,
                detail="Input cannot be None"
            )
        return func(self, input_data, *args, **kwargs)
    return wrapper