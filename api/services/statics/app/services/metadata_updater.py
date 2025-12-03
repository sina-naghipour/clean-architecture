import json
import os
from pathlib import Path
from datetime import datetime, UTC
from typing import Dict, Any
import uuid
from contextlib import contextmanager
from fastapi import HTTPException


class MetadataUpdater:
    def __init__(self, metadata_file: Path):
        self.metadata_file = metadata_file
        self.metadata_file.parent.mkdir(parents=True, exist_ok=True)
        
        if not self.metadata_file.exists():
            self._write_metadata({})
    
    def _read_metadata(self) -> Dict[str, Any]:
        try:
            if not self.metadata_file.exists():
                return {}
            
            with open(self.metadata_file, 'r') as f:
                content = f.read().strip()
                if not content:
                    return {}
                return json.loads(content)
        except (json.JSONDecodeError, IOError) as e:
            raise HTTPException(status_code=500, detail=f"Failed to read metadata: {str(e)}")
    
    def _write_metadata(self, metadata: Dict[str, Any]) -> bool:
        try:
            temp_file = self.metadata_file.with_suffix('.tmp')
            
            with open(temp_file, 'w') as f:
                json.dump(metadata, f, indent=2, default=str)
            
            os.replace(temp_file, self.metadata_file)
            return True
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to write metadata: {str(e)}")
    
    def add_file(self, file_id: str, file_data: Dict[str, Any]) -> bool:
        metadata = self._read_metadata()
        
        if "files" not in metadata:
            metadata["files"] = {}
        
        metadata["files"][file_id] = {
            **file_data,
            "id": file_id,
            "updated_at": datetime.now(UTC).isoformat()
        }
        
        return self._write_metadata(metadata)
    
    def remove_file(self, file_id: str) -> bool:
        metadata = self._read_metadata()
        
        if "files" in metadata and file_id in metadata["files"]:
            del metadata["files"][file_id]
            return self._write_metadata(metadata)
        
        return True
    
    def get_file(self, file_id: str) -> Dict[str, Any]:
        metadata = self._read_metadata()
        
        if "files" in metadata and file_id in metadata["files"]:
            return metadata["files"][file_id]
        
        raise HTTPException(status_code=404, detail="File not found in metadata")
    
    def list_files(self) -> Dict[str, Dict[str, Any]]:
        metadata = self._read_metadata()
        return metadata.get("files", {})
    
    def add_product_reference(self, product_id: str, file_id: str, product_name: str):
        metadata = self._read_metadata()
        
        if "products" not in metadata:
            metadata["products"] = {}
        
        if product_id not in metadata["products"]:
            metadata["products"][product_id] = {
                "id": product_id,
                "name": product_name,
                "files": [],
                "updated_at": datetime.now(UTC).isoformat()
            }
        
        if file_id not in metadata["products"][product_id]["files"]:
            metadata["products"][product_id]["files"].append(file_id)
        
        return self._write_metadata(metadata)
    
    def remove_product_reference(self, product_id: str, file_id: str):
        metadata = self._read_metadata()
        
        if "products" in metadata and product_id in metadata["products"]:
            if file_id in metadata["products"][product_id]["files"]:
                metadata["products"][product_id]["files"].remove(file_id)
                
                if not metadata["products"][product_id]["files"]:
                    del metadata["products"][product_id]
                
                return self._write_metadata(metadata)
        
        return True