import os
import shutil
import uuid
from typing import Optional, List
from pathlib import Path
import magic
from fastapi import UploadFile, HTTPException
import logging

from repositories.image_repository import ImageRepository
from repositories.product_repository import ProductRepository
from database.database_models import ImageDB
from database import pydantic_models
from decorators.product_image_service_decorators import (
    handle_image_errors, validate_product_exists, 
    validate_image_exists, validate_file_size,
    validate_image_format, validate_path_security,
    transaction_with_rollback
)

logger = logging.getLogger(__name__)

class ImageService:
    def __init__(self, 
                 image_repository: Optional[ImageRepository] = None,
                 product_repository: Optional[ProductRepository] = None):
        self.image_repository = image_repository or ImageRepository()
        self.product_repository = product_repository or ProductRepository()
        
        self.base_storage_path = Path(os.getenv("IMAGE_STORAGE_PATH", "/static/img"))
        self.max_file_size = 5 * 1024 * 1024
        self.allowed_mime_types = {
            "image/jpeg": ".jpg",
            "image/png": ".png", 
            "image/webp": ".webp"
        }
        
        self.base_storage_path.mkdir(parents=True, exist_ok=True)
    
    def _validate_file_path(self, filepath: Path) -> bool:
        try:
            absolute_path = filepath.resolve()
            allowed_path = self.base_storage_path.resolve()
            
            if not str(absolute_path).startswith(str(allowed_path)):
                logger.error(f"Path traversal attempt: {filepath}")
                return False
            
            if ".." in str(filepath) or filepath.is_absolute():
                logger.error(f"Invalid path pattern: {filepath}")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Path validation error: {e}")
            return False
    
    def _get_mime_type(self, file_content: bytes) -> Optional[str]:
        try:
            mime = magic.Magic(mime=True)
            return mime.from_buffer(file_content)
        except Exception as e:
            logger.error(f"MIME type detection failed: {e}")
            return None
    
    def _validate_image_content(self, file_content: bytes) -> bool:
        mime_type = self._get_mime_type(file_content)
        
        if not mime_type or mime_type not in self.allowed_mime_types:
            logger.error(f"Invalid MIME type: {mime_type}")
            return False
        
        return True
    
    def _generate_server_filename(self, product_id: str, mime_type: str) -> str:
        file_ext = self.allowed_mime_types.get(mime_type, ".jpg")
        unique_id = str(uuid.uuid4())[:8]
        return f"{product_id}_{unique_id}{file_ext}"
    
    @handle_image_errors
    @validate_product_exists()
    @validate_file_size()
    @validate_image_format
    async def upload_product_image(self, 
                                  product_id: str, 
                                  upload_file: UploadFile,
                                  is_primary: bool = False) -> Optional[pydantic_models.ProductImage]:
        
        mime_type = self._get_mime_type(await upload_file.read())
        await upload_file.seek(0)
        
        if not mime_type:
            raise HTTPException(status_code=400, detail="Could not determine file type")
        
        file_content = await upload_file.read()
        
        product_dir = self.base_storage_path / "products" / product_id
        product_dir.mkdir(parents=True, exist_ok=True)
        
        server_filename = self._generate_server_filename(product_id, mime_type)
        file_path = product_dir / server_filename
        
        if not self._validate_file_path(file_path):
            raise HTTPException(status_code=400, detail="Invalid file path")
        
        temp_file_path = file_path.with_suffix(".tmp")
        
        with open(temp_file_path, "wb") as f:
            f.write(file_content)
        
        os.rename(temp_file_path, file_path)
        
        from PIL import Image
        with Image.open(file_path) as img:
            width, height = img.size
        
        image_db = ImageDB(
            product_id=product_id,
            filename=server_filename,
            original_name=upload_file.filename,
            mime_type=mime_type,
            size=len(file_content),
            width=width,
            height=height,
            is_primary=is_primary
        )
        
        created_image = await self.image_repository.create_image(image_db)
        if not created_image:
            os.remove(file_path)
            raise HTTPException(status_code=500, detail="Failed to save image")
        
        await self.product_repository.add_image_to_product(product_id, created_image.id)
        
        if is_primary:
            await self.product_repository.set_primary_image(product_id, created_image.id)
            await self.image_repository.set_primary_image(product_id, created_image.id)
        
        image_url = f"/static/img/products/{product_id}/{server_filename}"
        
        return pydantic_models.ProductImage(
            id=created_image.id,
            product_id=product_id,
            filename=server_filename,
            original_name=upload_file.filename,
            mime_type=mime_type,
            size=len(file_content),
            width=width,
            height=height,
            is_primary=is_primary,
            url=image_url,
            uploaded_at=created_image.uploaded_at
        )
    
    @handle_image_errors
    @validate_product_exists()
    async def get_product_images(self, product_id: str) -> List[pydantic_models.ProductImage]:
        image_records = await self.image_repository.get_images_by_product_id(product_id)
        
        images = []
        for img in image_records:
            image_url = f"/static/img/products/{product_id}/{img.filename}"
            images.append(pydantic_models.ProductImage(
                id=img.id,
                product_id=img.product_id,
                filename=img.filename,
                original_name=img.original_name,
                mime_type=img.mime_type,
                size=img.size,
                width=img.width,
                height=img.height,
                is_primary=img.is_primary,
                url=image_url,
                uploaded_at=img.uploaded_at
            ))
        
        return images
    
    @handle_image_errors
    @validate_product_exists()
    @validate_image_exists()
    async def delete_product_image(self, product_id: str, image_id: str) -> bool:
        image = await self.image_repository.get_image_by_id(image_id)
        
        file_path = self.base_storage_path / "products" / product_id / image.filename
        
        if file_path.exists():
            file_path.unlink()
        
        deleted = await self.image_repository.delete_image(image_id)
        if deleted:
            await self.product_repository.remove_image_from_product(product_id, image_id)
        
        return deleted
    
    @handle_image_errors
    @validate_product_exists()
    async def set_primary_image(self, product_id: str, image_id: str) -> Optional[pydantic_models.ProductImage]:
        product = await self.product_repository.get_product_by_id(product_id)
        
        if image_id not in product.image_ids:
            raise HTTPException(status_code=400, detail="Image does not belong to product")
        
        success = await self.image_repository.set_primary_image(product_id, image_id)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to set primary image")
        
        await self.product_repository.set_primary_image(product_id, image_id)
        
        updated_image = await self.image_repository.get_image_by_id(image_id)
        
        image_url = f"/static/img/products/{product_id}/{updated_image.filename}"
        
        return pydantic_models.ProductImage(
            id=updated_image.id,
            product_id=updated_image.product_id,
            filename=updated_image.filename,
            original_name=updated_image.original_name,
            mime_type=updated_image.mime_type,
            size=updated_image.size,
            width=updated_image.width,
            height=updated_image.height,
            is_primary=updated_image.is_primary,
            url=image_url,
            uploaded_at=updated_image.uploaded_at
        )
    
    def _update_docusaurus_metadata(self, product_id: str):
        try:
            metadata_file = self.base_storage_path / "metadata.json"
            
            import json
            metadata = {}
            if metadata_file.exists():
                with open(metadata_file, "r") as f:
                    metadata = json.load(f)
            
            product_images = []
            for image_id in self.product_repository.get_product_by_id(product_id).image_ids:
                image = self.image_repository.get_image_by_id(image_id)
                if image:
                    product_images.append({
                        "id": image.id,
                        "url": f"/static/img/products/{product_id}/{image.filename}",
                        "is_primary": image.is_primary,
                        "width": image.width,
                        "height": image.height
                    })
            
            metadata[product_id] = product_images
            
            temp_file = metadata_file.with_suffix(".tmp")
            with open(temp_file, "w") as f:
                json.dump(metadata, f, indent=2)
            
            os.rename(temp_file, metadata_file)
            logger.info(f"Updated Docusaurus metadata for product {product_id}")
            
        except Exception as e:
            logger.error(f"Failed to update Docusaurus metadata: {e}")