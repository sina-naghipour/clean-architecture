import json
import logging
from pathlib import Path
from typing import Dict, Any, List
import os
from datetime import datetime

logger = logging.getLogger(__name__)

class MetadataGenerator:
    def __init__(self, base_storage_path: Path = None):
        self.base_storage_path = base_storage_path or Path(os.getenv("IMAGE_STORAGE_PATH", "/static/img"))
        self.metadata_file = self.base_storage_path / "metadata.json"
        
        self.base_storage_path.mkdir(parents=True, exist_ok=True)
    
    def _read_existing_metadata(self) -> Dict[str, Any]:
        try:
            if self.metadata_file.exists():
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
            return {}
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to read metadata file: {e}")
            raise
    
    def _write_metadata_atomic(self, metadata: Dict[str, Any]) -> bool:
        try:
            temp_file = self.metadata_file.with_suffix(".tmp")
            
            with open(temp_file, 'w') as f:
                json.dump(metadata, f, indent=2, default=str)
            
            temp_file.replace(self.metadata_file)
            logger.info(f"Metadata updated successfully: {self.metadata_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to write metadata file: {e}")
            return False
    
    def generate_product_metadata(self, 
                                 product_id: str, 
                                 product_name: str,
                                 images: List[Dict[str, Any]]) -> bool:
        try:
            metadata = self._read_existing_metadata()
            
            product_entry = {
                "id": product_id,
                "name": product_name,
                "images": images,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            metadata[product_id] = product_entry
            
            return self._write_metadata_atomic(metadata)
            
        except Exception as e:
            logger.error(f"Failed to generate product metadata: {e}")
            return False
    
    def update_product_images(self, 
                             product_id: str,
                             product_name: str,
                             image_data: Dict[str, Any],
                             operation: str = "add") -> bool:
        try:
            metadata = self._read_existing_metadata()
            
            if product_id not in metadata:
                metadata[product_id] = {
                    "id": product_id,
                    "name": product_name,
                    "images": [],
                    "created_at": datetime.utcnow().isoformat()
                }
            
            product_entry = metadata[product_id]
            product_entry["name"] = product_name
            product_entry["updated_at"] = datetime.utcnow().isoformat()
            
            if operation == "add":
                product_entry["images"].append(image_data)
            elif operation == "remove":
                product_entry["images"] = [
                    img for img in product_entry["images"] 
                    if img.get("id") != image_data.get("id")
                ]
            elif operation == "update_primary":
                for img in product_entry["images"]:
                    img["is_primary"] = (img.get("id") == image_data.get("id"))
            
            return self._write_metadata_atomic(metadata)
            
        except Exception as e:
            logger.error(f"Failed to update product images in metadata: {e}")
            return False
    
    def remove_product(self, product_id: str) -> bool:
        try:
            metadata = self._read_existing_metadata()
            
            if product_id in metadata:
                del metadata[product_id]
                return self._write_metadata_atomic(metadata)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove product from metadata: {e}")
            return False
    
    def get_product_metadata(self, product_id: str) -> Dict[str, Any]:
        try:
            metadata = self._read_existing_metadata()
            return metadata.get(product_id, {})
            
        except Exception as e:
            logger.error(f"Failed to get product metadata: {e}")
            return {}
    
    def get_all_metadata(self) -> Dict[str, Any]:
        try:
            return self._read_existing_metadata()
        except Exception as e:
            logger.error(f"Failed to get all metadata: {e}")
            return {}
    
    def validate_metadata_schema(self) -> bool:
        try:
            metadata = self._read_existing_metadata()
            
            required_product_fields = ["id", "name", "images", "updated_at"]
            required_image_fields = ["id", "url", "is_primary"]
            
            for product_id, product_data in metadata.items():
                for field in required_product_fields:
                    if field not in product_data:
                        logger.error(f"Missing field '{field}' in product {product_id}")
                        return False
                
                for image in product_data.get("images", []):
                    for field in required_image_fields:
                        if field not in image:
                            logger.error(f"Missing field '{field}' in image for product {product_id}")
                            return False
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to validate metadata schema: {e}")
            return False