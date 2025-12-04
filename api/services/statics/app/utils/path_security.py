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
        pass
    
    @validate_path_operation
    @prevent_path_traversal
    @ensure_within_base_dir
    def validate_and_sanitize(self, user_path: str, filename: str = None) -> Path:
        if user_path:
            user_path = user_path.strip('/\\')
        
        full_path = self.base_upload_dir
        
        if user_path:
            path_parts = [part for part in user_path.split('/') if part and part != '.']
            for part in path_parts:
                full_path = full_path / part
        
        if filename:
            full_path = full_path / filename
        
        if filename:
            full_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            full_path.mkdir(parents=True, exist_ok=True)
        
        return full_path
    
    @sanitize_filename
    def create_safe_filename(self, original_filename: str) -> str:
        _, ext = os.path.splitext(original_filename)
        
        if not ext:
            ext = ".bin"
        else:
            ext = ext.lower()
            
            if ext in ['.jpeg', '.jpg', '.jpe', '.jfif']:
                ext = '.jpg'
            elif ext in ['.tiff', '.tif']:
                ext = '.tiff'
            elif ext == '.htm':
                ext = '.html'
        
        safe_name = f"{uuid.uuid4().hex}{ext}"
        
        return safe_name
    
    @validate_path_operation
    @prevent_path_traversal
    @ensure_within_base_dir
    def get_relative_path(self, user_path: str) -> str:
        full_path = self.validate_and_sanitize(user_path)
        relative_path = full_path.relative_to(self.base_upload_dir)
        return str(relative_path)
    
    @validate_path_operation
    def is_safe_path(self, user_path: str) -> bool:
        try:
            self.validate_and_sanitize(user_path)
            return True
        except HTTPException:
            return False