import os
import magic
from fastapi import HTTPException


class FileValidator:
    def __init__(self, max_size: int, allowed_mime_types: list):
        self.max_size = max_size
        self.allowed_mime_types = allowed_mime_types
    
    def validate_size(self, file_content: bytes) -> bool:
        if len(file_content) > self.max_size:
            raise HTTPException(
                status_code=413,
                detail=f"File size exceeds maximum allowed size of {self.max_size // 1024 // 1024}MB"
            )
        return True
    
    def validate_magic_number(self, file_content: bytes) -> str:
        try:
            mime = magic.Magic(mime=True)
            detected_type = mime.from_buffer(file_content[:1024])
            
            if detected_type not in self.allowed_mime_types:
                raise HTTPException(
                    status_code=415,
                    detail=f"Invalid file type. Allowed: {', '.join(self.allowed_mime_types)}"
                )
            
            return detected_type
        except Exception:
            raise HTTPException(
                status_code=400,
                detail="Could not determine file type"
            )
    
    def validate_filename(self, filename: str) -> str:
        if not filename or filename.strip() == "":
            raise HTTPException(status_code=400, detail="Filename cannot be empty")
        
        filename = filename.strip()
        if len(filename) > 255:
            raise HTTPException(status_code=400, detail="Filename too long")
        
        return filename