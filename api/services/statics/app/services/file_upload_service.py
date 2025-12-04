import os
from pathlib import Path
from datetime import datetime
from typing import Optional
from fastapi import UploadFile

from utils.file_validator import FileValidator
from utils.path_security import PathSecurity
from utils.atomic_writer import AtomicWriter
from services.metadata_updater import MetadataUpdater
from decorators.statics_service_decorators import (
    handle_upload_errors,
    handle_delete_errors,
    handle_get_errors,
    validate_path_security
)


class FileUploadService:
    def __init__(
        self,
        upload_dir: Path,
        metadata_updater: MetadataUpdater,
        max_file_size: int,
        allowed_mime_types: list
    ):
        self.upload_dir = upload_dir
        self.metadata_updater = metadata_updater
        self.path_security = PathSecurity(upload_dir)
        self.file_validator = FileValidator(max_file_size, allowed_mime_types)
        
        self._ensure_upload_dir()
    
    @validate_path_security
    def _ensure_upload_dir(self):
        self.upload_dir.mkdir(parents=True, exist_ok=True)
    
    @handle_upload_errors
    async def upload_file(
        self,
        upload_file: UploadFile,
        subdirectory: str = "",
        custom_metadata: Optional[dict] = None
    ) -> dict:
        
        original_filename = self.file_validator.validate_filename(upload_file.filename)
        file_content = await upload_file.read()
        
        self.file_validator.validate_size(file_content)
        mime_type = self.file_validator.validate_magic_number(file_content)
        
        safe_filename = self.path_security.create_safe_filename(original_filename)
        full_path = self.path_security.validate_and_sanitize(subdirectory, safe_filename)
        
        with AtomicWriter.write_atomic(full_path) as temp_path:
            with open(temp_path, 'wb') as f:
                f.write(file_content)
        
        file_id = Path(safe_filename).stem
        relative_path = str(full_path.relative_to(self.upload_dir))
        
        file_data = {
            "original_filename": original_filename,
            "safe_filename": safe_filename,
            "path": relative_path,
            "full_path": str(full_path),
            "size_bytes": len(file_content),
            "mime_type": mime_type,
            "uploaded_at": datetime.utcnow().isoformat(),
            "custom_metadata": custom_metadata or {}
        }
        
        self.metadata_updater.add_file(file_id, file_data)
        
        return {
            "id": file_id,
            "filename": safe_filename,
            "original_filename": original_filename,
            "path": relative_path,
            "size": len(file_content),
            "mime_type": mime_type,
            "url": f"/static/img/{relative_path}"
        }
    
    @handle_delete_errors
    async def delete_file(self, file_id: str) -> bool:
        file_info = self.metadata_updater.get_file(file_id)
        file_path = self.upload_dir / file_info["path"]
        
        if AtomicWriter.delete_atomic(file_path):
            self.metadata_updater.remove_file(file_id)
            return True
        
        return False
    
    @handle_get_errors
    def get_file_path(self, file_id: str) -> Path:
        file_info = self.metadata_updater.get_file(file_id)
        return self.upload_dir / file_info["path"]
    
    @handle_get_errors
    def get_file_url(self, file_id: str) -> str:
        file_info = self.metadata_updater.get_file(file_id)
        return f"/static/img/{file_info['path']}"