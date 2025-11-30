from typing import List, Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorCollection
import logging
from datetime import datetime

from database.database_models import ImageDB
from database.connection import get_images_collection

logger = logging.getLogger(__name__)

class ImageRepository:
    def __init__(self, collection: AsyncIOMotorCollection = None):
        self.collection = collection
        self.logger = logger.getChild("ImageRepository")

    async def _get_collection(self) -> AsyncIOMotorCollection:
        if self.collection is None:
            self.collection = await get_images_collection()
        return self.collection

    async def create_image(self, image_data: ImageDB) -> Optional[ImageDB]:
        try:
            collection = await self._get_collection()
            self.logger.info(f"Creating image for product: {image_data.product_id}")
            
            image_dict = image_data.to_dict()
            result = await collection.insert_one(image_dict)
            
            if result.inserted_id:
                self.logger.info(f"Image created successfully with ID: {image_data.id}")
                return image_data
            else:
                self.logger.error("Failed to create image")
                return None
                
        except Exception as e:
            self.logger.error(f"Error creating image: {e}")
            raise

    async def get_image_by_id(self, image_id: str) -> Optional[ImageDB]:
        try:
            collection = await self._get_collection()
            self.logger.info(f"Fetching image by ID: {image_id}")
            
            image_data = await collection.find_one({"_id": image_id})
            
            if image_data:
                self.logger.info(f"Image found: {image_id}")
                return ImageDB.from_dict(image_data)
            else:
                self.logger.info(f"Image not found: {image_id}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error fetching image {image_id}: {e}")
            raise

    async def get_images_by_product_id(self, product_id: str) -> List[ImageDB]:
        try:
            collection = await self._get_collection()
            self.logger.info(f"Fetching images for product: {product_id}")
            
            cursor = collection.find({"product_id": product_id}).sort("uploaded_at", -1)
            images_data = await cursor.to_list(length=None)
            
            images = [ImageDB.from_dict(data) for data in images_data]
            self.logger.info(f"Found {len(images)} images for product {product_id}")
            
            return images
            
        except Exception as e:
            self.logger.error(f"Error fetching images for product {product_id}: {e}")
            raise

    async def get_primary_image_by_product_id(self, product_id: str) -> Optional[ImageDB]:
        try:
            collection = await self._get_collection()
            self.logger.info(f"Fetching primary image for product: {product_id}")
            
            image_data = await collection.find_one({
                "product_id": product_id,
                "is_primary": True
            })
            
            if image_data:
                self.logger.info(f"Primary image found for product: {product_id}")
                return ImageDB.from_dict(image_data)
            else:
                self.logger.info(f"No primary image found for product: {product_id}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error fetching primary image for product {product_id}: {e}")
            raise

    async def update_image(self, image_id: str, update_data: Dict[str, Any]) -> Optional[ImageDB]:
        try:
            collection = await self._get_collection()
            self.logger.info(f"Updating image: {image_id}")
            
            result = await collection.update_one(
                {"_id": image_id},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                self.logger.info(f"Image updated successfully: {image_id}")
                return await self.get_image_by_id(image_id)
            else:
                self.logger.info(f"No changes made to image: {image_id}")
                return await self.get_image_by_id(image_id)
                
        except Exception as e:
            self.logger.error(f"Error updating image {image_id}: {e}")
            raise

    async def delete_image(self, image_id: str) -> bool:
        try:
            collection = await self._get_collection()
            self.logger.info(f"Deleting image: {image_id}")
            
            result = await collection.delete_one({"_id": image_id})
            
            if result.deleted_count > 0:
                self.logger.info(f"Image deleted successfully: {image_id}")
                return True
            else:
                self.logger.info(f"Image not found for deletion: {image_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error deleting image {image_id}: {e}")
            raise

    async def set_primary_image(self, product_id: str, image_id: str) -> bool:
        try:
            collection = await self._get_collection()
            self.logger.info(f"Setting primary image {image_id} for product {product_id}")
            
            target_image = await collection.find_one({
                "_id": image_id,
                "product_id": product_id
            })
            
            if not target_image:
                self.logger.info(f"Image {image_id} not found for product {product_id}")
                return False
            
            await collection.update_many(
                {"product_id": product_id, "is_primary": True},
                {"$set": {"is_primary": False}}
            )
            
            result = await collection.update_one(
                {"_id": image_id},
                {"$set": {"is_primary": True}}
            )
            
            if result.modified_count > 0:
                self.logger.info(f"Primary image set to {image_id} for product {product_id}")
                return True
            else:
                self.logger.info(f"Failed to set primary image {image_id} for product {product_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error setting primary image for product {product_id}: {e}")
            raise
    async def count_images_by_product_id(self, product_id: str) -> int:
        try:
            collection = await self._get_collection()
            count = await collection.count_documents({"product_id": product_id})
            self.logger.debug(f"Counted {count} images for product {product_id}")
            return count
            
        except Exception as e:
            self.logger.error(f"Error counting images for product {product_id}: {e}")
            raise

    async def get_recent_images(self, limit: int = 20) -> List[ImageDB]:
        try:
            collection = await self._get_collection()
            self.logger.info(f"Fetching {limit} most recent images")
            
            cursor = collection.find({}).sort("uploaded_at", -1).limit(limit)
            images_data = await cursor.to_list(length=limit)
            
            images = [ImageDB.from_dict(data) for data in images_data]
            self.logger.info(f"Found {len(images)} recent images")
            
            return images
            
        except Exception as e:
            self.logger.error(f"Error fetching recent images: {e}")
            raise