from pathlib import Path
import os
import uuid
from fastapi import HTTPException
from decorators.statics_path_decorators import (
    validate_path_operation,
    prevent_path_traversal,
    ensure_within_base_dir,
    sanitize_filename,
    create_directory_if_missing
)


class PathSecurity:
    def __init__(self, base_upload_dir: Path):
        self.base_upload_dir = Path(base_upload_dir).resolve()
        self._ensure_base_directory()
    
    @create_directory_if_missing
    def _ensure_base_directory(self):
        """Ensure base directory exists (called by decorator)."""
        pass  # Decorator handles this
    
    @validate_path_operation
    @prevent_path_traversal
    @ensure_within_base_dir
    def validate_and_sanitize(self, user_path: str, filename: str = None) -> Path:
        """
        Validate and sanitize a user-provided path.
        
        Args:
            user_path: User-provided path (should be relative)
            filename: Optional filename to append
            
        Returns:
            Sanitized Path object guaranteed to be within base directory
        """
        # Normalize the path
        if user_path:
            # Remove leading/trailing slashes
            user_path = user_path.strip('/\\')
        
        # Create the full path
        full_path = self.base_upload_dir
        
        if user_path:
            # Split path parts and filter out empty parts
            path_parts = [part for part in user_path.split('/') if part and part != '.']
            for part in path_parts:
                full_path = full_path / part
        
        if filename:
            # Validate filename separately
            full_path = full_path / filename
        
        # Create directories if they don't exist
        if filename:
            full_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            full_path.mkdir(parents=True, exist_ok=True)
        
        return full_path
    
    @sanitize_filename
    def create_safe_filename(self, original_filename: str) -> str:
        """
        Create a safe filename from original filename.
        
        Args:
            original_filename: Original user-provided filename
            
        Returns:
            Safe filename with UUID and proper extension
        """
        # Extract and normalize extension
        _, ext = os.path.splitext(original_filename)
        
        if not ext:
            # No extension, use .bin as default
            ext = ".bin"
        else:
            # Normalize extension
            ext = ext.lower()
            
            # Normalize common image extensions
            if ext in ['.jpeg', '.jpg', '.jpe', '.jfif']:
                ext = '.jpg'
            elif ext in ['.tiff', '.tif']:
                ext = '.tiff'
            elif ext == '.htm':
                ext = '.html'
        
        # Generate safe filename with UUID
        safe_name = f"{uuid.uuid4().hex}{ext}"
        
        return safe_name
    
    @validate_path_operation
    @prevent_path_traversal
    @ensure_within_base_dir
    def get_relative_path(self, user_path: str) -> str:
        """
        Get relative path from base directory.
        
        Args:
            user_path: User-provided path
            
        Returns:
            Relative path string from base directory
        """
        full_path = self.validate_and_sanitize(user_path)
        relative_path = full_path.relative_to(self.base_upload_dir)
        return str(relative_path)
    
    @validate_path_operation
    def is_safe_path(self, user_path: str) -> bool:
        """
        Check if a path is safe (within base directory).
        
        Args:
            user_path: Path to check
            
        Returns:
            True if path is safe, False otherwise
        """
        try:
            self.validate_and_sanitize(user_path)
            return True
        except HTTPException:
            return False