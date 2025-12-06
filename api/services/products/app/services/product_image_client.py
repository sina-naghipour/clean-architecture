# clients/product_image_client.py
import httpx
import asyncio
from typing import List, Optional, Dict, Any
from fastapi import UploadFile
from dataclasses import dataclass
import logging


@dataclass
class UploadResult:
    success: bool
    url: Optional[str] = None
    error: Optional[str] = None


class ProductImageClient:
    def __init__(
        self,
        base_url: str,
        timeout: float = 30.0,
        max_concurrent: int = 10,
        logger: Optional[logging.Logger] = None
    ):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.max_concurrent = max_concurrent
        self.logger = logger or logging.getLogger(__name__)
        
        self.client = httpx.AsyncClient(timeout=timeout)
    
    async def close(self):
        await self.client.aclose()
    
    async def upload_image(
        self,
        file: UploadFile,
        subdirectory: str = "products",
        metadata: Optional[Dict[str, Any]] = None
    ) -> UploadResult:
        try:
            # Prepare files and params
            files = {'file': (file.filename, await file.read(), file.content_type)}
            params = {'subdirectory': subdirectory}
            
            if metadata:
                import json
                params['custom_metadata'] = json.dumps(metadata)
            
            # Make request
            response = await self.client.post(
                f"{self.base_url}/files",
                files=files,
                params=params
            )
            
            if response.status_code == 201:
                data = response.json()
                return UploadResult(
                    success=True,
                    url=data.get('url')
                )
            else:
                error_msg = response.json().get('detail', 'Upload failed')
                self.logger.error(f"Upload failed: {error_msg}")
                return UploadResult(success=False, error=error_msg)
                
        except Exception as e:
            self.logger.error(f"Upload exception: {str(e)}")
            return UploadResult(success=False, error=str(e))
    
    async def upload_images(
        self,
        files: List[UploadFile],
        subdirectory: str = "products",
        metadata_list: Optional[List[Dict[str, Any]]] = None
    ) -> List[UploadResult]:
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def upload_with_limit(file: UploadFile, idx: int):
            async with semaphore:
                metadata = metadata_list[idx] if metadata_list and idx < len(metadata_list) else None
                return await self.upload_image(file, subdirectory, metadata)
        
        tasks = [upload_with_limit(file, i) for i, file in enumerate(files)]
        return await asyncio.gather(*tasks)
    
    async def delete_image(self, file_id: str) -> bool:
        try:
            response = await self.client.delete(f"{self.base_url}/files/{file_id}")
            if response.status_code == 204:
                return True
            elif response.status_code == 404:
                self.logger.warning(f"Image not found: {file_id}")
                return False
            return False
        except Exception as e:
            self.logger.error(f"Delete failed: {str(e)}")
            return False
    
    async def delete_images(self, file_ids: List[str]) -> List[bool]:
        tasks = [self.delete_image(file_id) for file_id in file_ids]
        return await asyncio.gather(*tasks)
    
    async def validate_image(self, image_url: str) -> bool:
        try:
            if '/static/img/' in image_url:
                filename = image_url.split('/')[-1]
                file_id = filename.split('.')[0]
                print(f"{self.base_url}/files/{file_id}")
                response = await self.client.get(f"{self.base_url}/files/{file_id}")
                return response.status_code == 200
            
            elif image_url.startswith('http'):
                response = await self.client.get(image_url, timeout=5.0)
                return response.status_code == 200
            
            return False
            
        except Exception:
            return False

    def extract_file_id(self, image_url: str) -> Optional[str]:
        try:
            if '/static/img/' in image_url:
                return image_url.split('/')[-1].split('.')[0]
            return None
        except Exception:
            return None
    
    async def cleanup_unused_images(
        self,
        used_image_urls: List[str],
        subdirectory: str = "products"
    ) -> List[str]:
        try:
            response = await self.client.get(
                f"{self.base_url}/metadata",
                params={"subdirectory": subdirectory}
            )
            
            if response.status_code == 200:
                data = response.json()
                used_ids = {self.extract_file_id(url) for url in used_image_urls}
                
                deleted_ids = []
                for file_info in data.get('files', []):
                    file_id = file_info.get('id')
                    if file_id and file_id not in used_ids:
                        if await self.delete_image(file_id):
                            deleted_ids.append(file_id)
                
                return deleted_ids
                
        except Exception as e:
            self.logger.error(f"Cleanup failed: {str(e)}")
        
        return []