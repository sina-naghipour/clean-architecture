from typing import List, Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorCollection
import logging

from database.database_models import ImageDB
from database.connection import get_images_collection
from decorators.product_image_repository_decorators import (
    handle_repository_errors, ensure_collection,
    log_operation, validate_image_id, validate_product_id,
    transaction_safe, validate_image_id_set_primary_image,
    validate_product_id_set_primary_image
)

logger = logging.getLogger(__name__)

class ImageRepository:
    def __init__(self, collection: AsyncIOMotorCollection = None):
        self.collection = collection
        self.logger = logger.getChild("ImageRepository")

    async def _get_collection(self) -> AsyncIOMotorCollection:
        if self.collection is None:
            self.collection = await get_images_collection()
        return self.collection

    @handle_repository_errors
    @ensure_collection
    @log_operation("create_image")
    async def create_image(self, image_data: ImageDB) -> Optional[ImageDB]:
        image_dict = image_data.to_dict()
        result = await self.collection.insert_one(image_dict)
        
        if result.inserted_id:
            return image_data
        return None

    @handle_repository_errors
    @ensure_collection
    @log_operation("get_image_by_id")
    @validate_image_id
    async def get_image_by_id(self, image_id: str) -> Optional[ImageDB]:
        image_data = await self.collection.find_one({"_id": image_id})
        
        if image_data:
            return ImageDB.from_dict(image_data)
        return None

    @handle_repository_errors
    @ensure_collection
    @log_operation("get_images_by_product_id")
    @validate_product_id
    async def get_images_by_product_id(self, product_id: str) -> List[ImageDB]:
        cursor = self.collection.find({"product_id": product_id}).sort("uploaded_at", -1)
        images_data = await cursor.to_list(length=None)
        
        return [ImageDB.from_dict(data) for data in images_data]

    @handle_repository_errors
    @ensure_collection
    @log_operation("get_primary_image_by_product_id")
    @validate_product_id
    async def get_primary_image_by_product_id(self, product_id: str) -> Optional[ImageDB]:
        image_data = await self.collection.find_one({
            "product_id": product_id,
            "is_primary": True
        })
        
        if image_data:
            return ImageDB.from_dict(image_data)
        return None

    @handle_repository_errors
    @ensure_collection
    @log_operation("update_image")
    @validate_image_id
    async def update_image(self, image_id: str, update_data: Dict[str, Any]) -> Optional[ImageDB]:
        result = await self.collection.update_one(
            {"_id": image_id},
            {"$set": update_data}
        )
        
        if result.modified_count > 0:
            return await self.get_image_by_id(image_id)
        return await self.get_image_by_id(image_id)

    @handle_repository_errors
    @ensure_collection
    @log_operation("delete_image")
    @validate_image_id
    async def delete_image(self, image_id: str) -> bool:
        result = await self.collection.delete_one({"_id": image_id})
        return result.deleted_count > 0

    @handle_repository_errors
    @ensure_collection
    @transaction_safe
    @log_operation("set_primary_image")
    @validate_image_id_set_primary_image
    @validate_product_id_set_primary_image
    async def set_primary_image(self, product_id: str, image_id: str) -> bool:
        target_image = await self.collection.find_one({
            "_id": image_id,
            "product_id": product_id
        })
        
        if not target_image:
            return False
        
        await self.collection.update_many(
            {"product_id": product_id, "is_primary": True},
            {"$set": {"is_primary": False}}
        )
        
        result = await self.collection.update_one(
            {"_id": image_id},
            {"$set": {"is_primary": True}}
        )
        
        return result.modified_count > 0

    @handle_repository_errors
    @ensure_collection
    @log_operation("count_images_by_product_id")
    @validate_product_id
    async def count_images_by_product_id(self, product_id: str) -> int:
        count = await self.collection.count_documents({"product_id": product_id})
        return count

    @handle_repository_errors
    @ensure_collection
    @log_operation("get_recent_images")
    async def get_recent_images(self, limit: int = 20) -> List[ImageDB]:
        cursor = self.collection.find({}).sort("uploaded_at", -1).limit(limit)
        images_data = await cursor.to_list(length=limit)
        
        return [ImageDB.from_dict(data) for data in images_data]