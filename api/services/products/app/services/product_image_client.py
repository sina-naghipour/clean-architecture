import asyncio
from typing import List, Optional, Dict, Any
from fastapi import UploadFile
from dataclasses import dataclass
import logging
import json
import httpx

from utils.http_client import ResilientHttpClient
from utils.resilience_config import ResilienceConfig


@dataclass
class UploadResult:
    success: bool
    url: Optional[str] = None
    error: Optional[str] = None


class ProductImageClient:
    def __init__(
        self,
        base_url: str,
        resilience_config: Optional[ResilienceConfig] = None,
        max_concurrent: int = 10,
        logger: Optional[logging.Logger] = None
    ):
        self.base_url = base_url.rstrip('/')
        self.max_concurrent = max_concurrent
        self.logger = logger or logging.getLogger(__name__)
        
        if resilience_config is None:
            resilience_config = ResilienceConfig()
        
        self.http_client = ResilientHttpClient(resilience_config, logger=self.logger)
    
    async def close(self):
        try:
            await self.http_client.close()
        except Exception as e:
            self.logger.error(f"Error closing ProductImageClient: {str(e)}")
    
    async def upload_image(
        self,
        file: UploadFile,
        subdirectory: str = "products",
        metadata: Optional[Dict[str, Any]] = None,
        token: str = None
    ) -> UploadResult:
        try:
            self.logger.info(f"Uploading image: {file.filename} to {subdirectory}")
            files = {'file': (file.filename, await file.read(), file.content_type)}
            params = {'subdirectory': subdirectory}
            headers = {}
            
            if token:
                headers['Authorization'] = f'Bearer {token}'
            if metadata:
                params['custom_metadata'] = json.dumps(metadata)
            
            response = await self.http_client.post(
                f"{self.base_url}/files",
                files=files,
                params=params,
                headers=headers
            )
            
            if response.status_code == 201:
                data = response.json()
                url = data.get('url')
                self.logger.info(f"Image uploaded successfully: {url}")
                return UploadResult(success=True, url=url)
            else:
                error_msg = response.json().get('detail', 'Upload failed')
                self.logger.error(f"Upload failed with status {response.status_code}: {error_msg}")
                return UploadResult(success=False, error=error_msg)
                
        except httpx.RequestError as e:
            self.logger.error(f"Network error during upload: {str(e)}")
            return UploadResult(success=False, error=f"Network error: {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error during upload: {str(e)}", exc_info=True)
            return UploadResult(success=False, error=f"Upload exception: {str(e)}")
    
    async def upload_images(
        self,
        files: List[UploadFile],
        subdirectory: str = "products",
        metadata_list: Optional[List[Dict[str, Any]]] = None,
        token: str = None
    ) -> List[UploadResult]:
        self.logger.info(f"Uploading {len(files)} images to {subdirectory}")
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def upload_with_limit(file: UploadFile, idx: int):
            async with semaphore:
                metadata = metadata_list[idx] if metadata_list and idx < len(metadata_list) else None
                return await self.upload_image(file, subdirectory, metadata, token)
        
        tasks = [upload_with_limit(file, i) for i, file in enumerate(files)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"Upload task {i} failed: {str(result)}")
                final_results.append(UploadResult(success=False, error=str(result)))
            else:
                final_results.append(result)
        
        success_count = sum(1 for r in final_results if r.success)
        self.logger.info(f"Upload batch complete: {success_count}/{len(files)} successful")
        return final_results
    
    async def delete_image(self, file_id: str, token: str = None) -> bool:
        try:
            self.logger.info(f"Deleting image: {file_id}")
            headers = {}
            if token:
                headers['Authorization'] = f'Bearer {token}'
            
            response = await self.http_client.delete(
                f"{self.base_url}/files/{file_id}",
                headers=headers
            )
            
            if response.status_code == 204:
                self.logger.info(f"Image deleted successfully: {file_id}")
                return True
            elif response.status_code == 404:
                self.logger.warning(f"Image not found: {file_id}")
                return False
            else:
                self.logger.error(f"Delete failed with status {response.status_code}: {response.text}")
                return False
        except httpx.RequestError as e:
            self.logger.error(f"Network error during delete: {str(e)}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error during delete: {str(e)}", exc_info=True)
            return False
    
    async def delete_images(self, file_ids: List[str], token: str = None) -> List[bool]:
        self.logger.info(f"Deleting {len(file_ids)} images")
        tasks = [self.delete_image(file_id, token) for file_id in file_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"Delete task for {file_ids[i]} failed: {str(result)}")
                final_results.append(False)
            else:
                final_results.append(result)
        
        success_count = sum(1 for r in final_results if r)
        self.logger.info(f"Delete batch complete: {success_count}/{len(file_ids)} successful")
        return final_results
    
    async def validate_image(self, image_url: str, token: str = None) -> bool:
        try:
            self.logger.debug(f"Validating image: {image_url}")
            if '/static/img/' in image_url:
                filename = image_url.split('/')[-1]
                file_id = filename.split('.')[0]
                
                headers = {}
                if token:
                    headers['Authorization'] = f'Bearer {token}'
                
                response = await self.http_client.get(
                    f"{self.base_url}/files/{file_id}",
                    headers=headers
                )
                is_valid = response.status_code == 200
                self.logger.debug(f"Image validation result: {is_valid}")
                return is_valid
            
            elif image_url.startswith('http'):
                response = await self.http_client.get(image_url)
                is_valid = response.status_code == 200
                self.logger.debug(f"External image validation result: {is_valid}")
                return is_valid
            
            self.logger.warning(f"Unsupported image URL format: {image_url}")
            return False
            
        except httpx.RequestError as e:
            self.logger.error(f"Network error during validation: {str(e)}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error during validation: {str(e)}", exc_info=True)
            return False
    
    def extract_file_id(self, image_url: str) -> Optional[str]:
        try:
            if '/static/img/' in image_url:
                return image_url.split('/')[-1].split('.')[0]
            return None
        except Exception as e:
            self.logger.error(f"Error extracting file ID from {image_url}: {str(e)}")
            return None
    
    async def cleanup_unused_images(
        self,
        used_image_urls: List[str],
        subdirectory: str = "products",
        token: str = None
    ) -> List[str]:
        try:
            self.logger.info(f"Cleaning up unused images in {subdirectory}")
            response = await self.http_client.get(
                f"{self.base_url}/metadata",
                params={"subdirectory": subdirectory}
            )
            
            if response.status_code == 200:
                data = response.json()
                used_ids = {self.extract_file_id(url) for url in used_image_urls}
                
                files_to_check = data.get('files', [])
                self.logger.info(f"Found {len(files_to_check)} files to check")
                
                deleted_ids = []
                for file_info in files_to_check:
                    file_id = file_info.get('id')
                    if file_id and file_id not in used_ids:
                        if await self.delete_image(file_id, token):
                            deleted_ids.append(file_id)
                
                self.logger.info(f"Cleanup complete: deleted {len(deleted_ids)} files")
                return deleted_ids
            else:
                self.logger.error(f"Failed to fetch metadata: {response.status_code}")
                return []
                
        except httpx.RequestError as e:
            self.logger.error(f"Network error during cleanup: {str(e)}")
            return []
        except Exception as e:
            self.logger.error(f"Unexpected error during cleanup: {str(e)}", exc_info=True)
            return []
    
    def get_circuit_state(self):
        return self.http_client.get_circuit_state()