import os
import magic
from fastapi import HTTPException
from decorators.statics_validator_decorators import (
    with_size_validation,
    with_type_validation,
    with_filename_validation,
    validate_input_not_none,
    handle_validation_errors
)


class FileValidator:
    def __init__(self, max_size: int, allowed_mime_types: list):
        self.max_size = max_size
        self.allowed_mime_types = allowed_mime_types
    
    @with_size_validation
    @validate_input_not_none
    @handle_validation_errors
    def validate_size(self, file_content: bytes) -> bool:
        """Validate file size."""
        if len(file_content) > self.max_size:
            raise HTTPException(
                status_code=413,
                detail=f"File size ({len(file_content)} bytes) exceeds maximum allowed size ({self.max_size} bytes)"
            )
        return True
    
    @with_type_validation
    @validate_input_not_none
    @handle_validation_errors
    def validate_magic_number(self, file_content: bytes) -> str:
        """Validate file type using magic numbers."""
        try:
            # Use magic library to detect MIME type
            mime_type = magic.from_buffer(file_content[:1024], mime=True)
            
            if mime_type not in self.allowed_mime_types:
                raise HTTPException(
                    status_code=415,
                    detail=f"File type '{mime_type}' is not allowed. Allowed types: {', '.join(self.allowed_mime_types)}"
                )
            
            return mime_type
            
        except magic.MagicException as e:
            raise HTTPException(
                status_code=400,
                detail=f"Could not determine file type: {str(e)}"
            )
        except Exception as e:
            # Fallback to content type if magic fails
            raise HTTPException(
                status_code=415,
                detail=f"File type validation failed: {str(e)}"
            )
    
    @with_filename_validation
    @validate_input_not_none
    @handle_validation_errors
    def validate_filename(self, filename: str) -> str:
        """Validate and sanitize filename."""
        if not filename or filename.strip() == "":
            raise HTTPException(
                status_code=422,
                detail="Filename cannot be empty"
            )
        
        filename = filename.strip()
        
        # Check length
        if len(filename) > 255:
            raise HTTPException(
                status_code=422,
                detail="Filename too long (maximum 255 characters)"
            )
        
        # Check for dangerous characters
        dangerous_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|', '\0']
        for char in dangerous_chars:
            if char in filename:
                raise HTTPException(
                    status_code=422,
                    detail=f"Filename contains invalid character: {repr(char)}"
                )
        
        # Check for path traversal attempts
        if '..' in filename:
            raise HTTPException(
                status_code=422,
                detail="Filename contains path traversal attempt"
            )
        
        # Check for reserved names (Windows + Unix)
        reserved_names = [
            'CON', 'PRN', 'AUX', 'NUL',
            'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
            'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
        ]
        name_without_ext = os.path.splitext(filename)[0].upper()
        if name_without_ext in reserved_names:
            raise HTTPException(
                status_code=422,
                detail=f"Filename '{name_without_ext}' is a reserved system name"
            )
        
        return filename
    
    @handle_validation_errors
    def validate_extension(self, filename: str, allowed_extensions: list = None) -> str:
        """Validate file extension (optional)."""
        if allowed_extensions is None:
            allowed_extensions = ['.jpg', '.jpeg', '.png', '.webp']
        
        _, ext = os.path.splitext(filename)
        ext = ext.lower()
        
        if ext not in allowed_extensions:
            raise HTTPException(
                status_code=422,
                detail=f"File extension '{ext}' is not allowed. Allowed: {', '.join(allowed_extensions)}"
            )
        
        return ext