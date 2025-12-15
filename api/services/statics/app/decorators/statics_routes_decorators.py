from functools import wraps
from typing import Callable
from fastapi import HTTPException, Request
from api.services.statics.app.services.statics_helpers import create_problem_response


# Error type URIs from your catalog
ERROR_TYPES = {
    "bad-request": "https://example.com/errors/bad-request",
    "unauthorized": "https://example.com/errors/unauthorized",
    "forbidden": "https://example.com/errors/forbidden",
    "not-found": "https://example.com/errors/not-found",
    "conflict": "https://example.com/errors/conflict",
    "file-too-large": "https://example.com/errors/file-too-large",
    "unsupported-media-type": "https://example.com/errors/unsupported-media-type",
    "validation": "https://example.com/errors/validation",
    "internal": "https://example.com/errors/internal",
    "multi-status": "https://example.com/errors/multi-status"
}


def _map_http_exception_to_problem(he: HTTPException, request_url: str):
    """Map HTTPException to proper problem details based on status code."""
    status_code = he.status_code
    
    # Map status codes to error types
    if status_code == 400:
        error_type = "bad-request"
        title = "Bad Request"
    elif status_code == 401:
        error_type = "unauthorized"
        title = "Unauthorized"
    elif status_code == 403:
        error_type = "forbidden"
        title = "Forbidden"
    elif status_code == 404:
        error_type = "not-found"
        title = "Not Found"
    elif status_code == 409:
        error_type = "conflict"
        title = "Conflict"
    elif status_code == 413:
        error_type = "file-too-large"
        title = "File Too Large"
    elif status_code == 415:
        error_type = "unsupported-media-type"
        title = "Unsupported Media Type"
    elif status_code == 422:
        error_type = "validation"
        title = "Validation Failed"
    else:
        error_type = "internal"
        title = "Internal Server Error"
    
    return create_problem_response(
        status_code=status_code,
        error_type=error_type,
        title=title,
        detail=he.detail,
        instance=str(request_url)
    )


def handle_file_upload_errors(func: Callable) -> Callable:
    """Decorator to handle errors for file upload endpoints."""
    @wraps(func)
    async def wrapper(request: Request, *args, **kwargs):
        try:
            return await func(request, *args, **kwargs)
        except HTTPException as he:
            return _map_http_exception_to_problem(he, request.url)
        except Exception as e:
            return create_problem_response(
                status_code=500,
                error_type="internal",
                title="Internal Server Error",
                detail=f"An unexpected error occurred: {str(e)}",
                instance=str(request.url)
            )
    return wrapper


def handle_file_operation_errors(func: Callable) -> Callable:
    """Decorator to handle errors for file retrieval/deletion endpoints."""
    @wraps(func)
    async def wrapper(request: Request, *args, **kwargs):
        try:
            return await func(request, *args, **kwargs)
        except HTTPException as he:
            return _map_http_exception_to_problem(he, request.url)
        except Exception as e:
            return create_problem_response(
                status_code=500,
                error_type="internal",
                title="Internal Server Error",
                detail=f"An unexpected error occurred: {str(e)}",
                instance=str(request.url)
            )
    return wrapper


def handle_metadata_errors(func: Callable) -> Callable:
    """Decorator to handle errors for metadata operations."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except HTTPException as he:
            return _map_http_exception_to_problem(he, "")
        except Exception as e:
            return create_problem_response(
                status_code=500,
                error_type="internal",
                title="Internal Server Error",
                detail=f"An unexpected error occurred: {str(e)}",
                instance=""
            )
    return wrapper


def handle_batch_upload_errors(func: Callable) -> Callable:
    """Decorator to handle batch upload with multi-status reporting."""
    @wraps(func)
    async def wrapper(request: Request, *args, **kwargs):
        try:
            return await func(request, *args, **kwargs)
        except Exception as e:
            # For batch operations, return 207 multi-status even for top-level errors
            files = kwargs.get('files', [])
            
            # Create proper multi-status response
            failed_files = []
            for file in files:
                filename = file.filename if hasattr(file, 'filename') else "unknown"
                failed_files.append({
                    "filename": filename,
                    "error": f"Batch operation failed: {str(e)}",
                    "status_code": 500
                })
            
            # Return as proper multi-status response
            return {
                "type": ERROR_TYPES["multi-status"],
                "title": "Multi-Status",
                "status": 207,
                "detail": "Batch operation completed with partial success",
                "instance": str(request.url),
                "successful_count": 0,
                "failed_count": len(failed_files),
                "successful": [],
                "failed": failed_files
            }
    return wrapper