from pathlib import Path
from fastapi import HTTPException


class PathSecurity:
    def __init__(self, base_upload_dir: Path):
        self.base_upload_dir = base_upload_dir.resolve()
        self.base_upload_dir.mkdir(parents=True, exist_ok=True)
    
    def validate_and_sanitize(self, user_path: str, filename: str = None) -> Path:
        if not user_path:
            raise HTTPException(status_code=400, detail="Path cannot be empty")
        
        if ".." in user_path:
            raise HTTPException(status_code=400, detail="Path traversal detected")
        
        if "%" in user_path:
            decoded = user_path.replace("%2e", ".").replace("%2E", ".")
            if ".." in decoded:
                raise HTTPException(status_code=400, detail="Encoded path traversal detected")
        
        if user_path.startswith("/") or ":" in user_path:
            raise HTTPException(status_code=400, detail="Absolute paths not allowed")
        
        try:
            full_path = (self.base_upload_dir / user_path).resolve()
            
            if filename:
                full_path = full_path / filename
            
            if not str(full_path).startswith(str(self.base_upload_dir)):
                raise HTTPException(status_code=400, detail="Path outside allowed directory")
            
            return full_path
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid path")
    
    def create_safe_filename(self, original_filename: str) -> str:
        import uuid
        import os
        
        ext = os.path.splitext(original_filename)[1]
        if not ext:
            ext = ".bin"
        
        safe_ext = ext.lower()
        if safe_ext in [".jpeg", ".jpg"]:
            safe_ext = ".jpg"
        
        return f"{uuid.uuid4().hex}{safe_ext}"