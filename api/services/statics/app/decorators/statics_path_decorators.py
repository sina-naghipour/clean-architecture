from functools import wraps
from typing import Callable
from fastapi import HTTPException
from pathlib import Path


def validate_path_operation(func: Callable) -> Callable:
    """Decorator for path validation and sanitization operations."""
    @wraps(func)
    def wrapper(self, user_path: str, *args, **kwargs):
        try:
            # Pre-validation checks
            if not user_path:
                user_path = ""  # Handle empty path
            
            # Ensure path is string
            if not isinstance(user_path, str):
                raise HTTPException(
                    status_code=422,
                    detail="Path must be a string"
                )
            
            return func(self, user_path, *args, **kwargs)
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Path validation failed: {str(e)}"
            )
    return wrapper


def prevent_path_traversal(func: Callable) -> Callable:
    """Decorator specifically to prevent path traversal attacks."""
    @wraps(func)
    def wrapper(self, user_path: str, *args, **kwargs):
        # Check for obvious path traversal
        if ".." in user_path:
            raise HTTPException(
                status_code=400,
                detail="Path traversal detected (..)"
            )
        
        # Check for URL encoded traversal
        if "%" in user_path:
            decoded = user_path.replace("%2e", ".").replace("%2E", ".")
            if ".." in decoded:
                raise HTTPException(
                    status_code=400,
                    detail="Encoded path traversal detected"
                )
        
        # Check for absolute paths
        if user_path.startswith("/") or ":" in user_path:
            raise HTTPException(
                status_code=400,
                detail="Absolute paths not allowed"
            )
        
        # Check for null bytes (C-style string termination attacks)
        if "\0" in user_path:
            raise HTTPException(
                status_code=400,
                detail="Null byte detected in path"
            )
        
        # Check for control characters
        if any(ord(c) < 32 for c in user_path):
            raise HTTPException(
                status_code=400,
                detail="Control characters detected in path"
            )
        
        return func(self, user_path, *args, **kwargs)
    return wrapper


def ensure_within_base_dir(func: Callable) -> Callable:
    """Decorator to ensure final path is within base directory."""
    @wraps(func)
    def wrapper(self, user_path: str, *args, **kwargs):
        try:
            result = func(self, user_path, *args, **kwargs)
            
            # Verify the result is within base directory
            if isinstance(result, Path):
                base_dir = Path(self.base_upload_dir).resolve()
                result_path = result.resolve()
                
                # Check if result is within base directory
                try:
                    result_path.relative_to(base_dir)
                except ValueError:
                    raise HTTPException(
                        status_code=400,
                        detail="Path would be outside allowed directory"
                    )
                
                # Additional security: check for symlinks
                if result_path.is_symlink():
                    raise HTTPException(
                        status_code=400,
                        detail="Symbolic links are not allowed"
                    )
            
            return result
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Path containment check failed: {str(e)}"
            )
    return wrapper


def sanitize_filename(func: Callable) -> Callable:
    """Decorator for filename sanitization operations."""
    @wraps(func)
    def wrapper(self, original_filename: str, *args, **kwargs):
        try:
            # Validate input
            if not original_filename:
                raise HTTPException(
                    status_code=422,
                    detail="Filename cannot be empty"
                )
            
            if not isinstance(original_filename, str):
                raise HTTPException(
                    status_code=422,
                    detail="Filename must be a string"
                )
            
            return func(self, original_filename, *args, **kwargs)
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Filename sanitization failed: {str(e)}"
            )
    return wrapper


def create_directory_if_missing(func: Callable) -> Callable:
    """Decorator to ensure base directory exists before operations."""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            # Ensure base directory exists
            if hasattr(self, 'base_upload_dir'):
                base_dir = Path(self.base_upload_dir)
                base_dir.mkdir(parents=True, exist_ok=True)
                
                # Verify it's a directory
                if not base_dir.is_dir():
                    raise HTTPException(
                        status_code=500,
                        detail=f"Base upload path is not a directory: {base_dir}"
                    )
            
            return func(self, *args, **kwargs)
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Directory setup failed: {str(e)}"
            )
    return wrapper