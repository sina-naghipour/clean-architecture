from typing import List, Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorCollection
from bson import ObjectId
import logging
from datetime import datetime

from database.database_models import ProductDB
from database.connection import get_products_collection

logger = logging.getLogger(__name__)

class ProductRepository:
    def __init__(self, collection: AsyncIOMotorCollection = None):
        self.collection = collection
        self.logger = logger.getChild("ProductRepository")

    async def _get_collection(self) -> AsyncIOMotorCollection:
        if self.collection is None:
            self.collection = await get_products_collection()
        return self.collection

    async def create_product(self, product_data: ProductDB) -> Optional[ProductDB]:
        try:
            collection = await self._get_collection()
            self.logger.info(f"Creating product: {product_data.name}")
            
            existing_product = await collection.find_one({
                "name": {"$regex": f"^{product_data.name}$", "$options": "i"}
            })
            
            if existing_product:
                self.logger.warning(f"Product with name '{product_data.name}' already exists")
                return None
            
            product_dict = product_data.to_dict()
            result = await collection.insert_one(product_dict)
            
            if result.inserted_id:
                self.logger.info(f"Product created successfully with ID: {product_data.id}")
                return product_data
            else:
                self.logger.error("Failed to create product")
                return None
                
        except Exception as e:
            self.logger.error(f"Error creating product: {e}")
            raise

    async def get_product_by_id(self, product_id: str) -> Optional[ProductDB]:
        try:
            collection = await self._get_collection()
            self.logger.info(f"Fetching product by ID: {product_id}")
            
            product_data = await collection.find_one({"_id": product_id})
            
            if product_data:
                self.logger.info(f"Product found: {product_id}")
                return ProductDB.from_dict(product_data)
            else:
                self.logger.info(f"Product not found: {product_id}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error fetching product {product_id}: {e}")
            raise

    async def get_product_by_name(self, name: str) -> Optional[ProductDB]:
        try:
            collection = await self._get_collection()
            self.logger.info(f"Fetching product by name: {name}")
            
            product_data = await collection.find_one({
                "name": {"$regex": f"^{name}$", "$options": "i"}
            })
            
            if product_data:
                self.logger.info(f"Product found by name: {name}")
                return ProductDB.from_dict(product_data)
            else:
                self.logger.info(f"Product not found by name: {name}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error fetching product by name {name}: {e}")
            raise

    async def list_products(
        self, 
        skip: int = 0, 
        limit: int = 20,
        search_query: Optional[str] = None,
        tags: Optional[List[str]] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None
    ) -> List[ProductDB]:
        try:
            collection = await self._get_collection()
            self.logger.info(f"Listing products - skip: {skip}, limit: {limit}, search: {search_query}, tags: {tags}, min_price: {min_price}, max_price: {max_price}")
            
            query = {}
            
            if search_query:
                query["$or"] = [
                    {"name": {"$regex": search_query, "$options": "i"}},
                    {"description": {"$regex": search_query, "$options": "i"}}
                ]
            
            if tags:
                query["tags"] = {"$in": tags}
            
            price_filter = {}
            if min_price is not None:
                price_filter["$gte"] = min_price
            if max_price is not None:
                price_filter["$lte"] = max_price
            
            if price_filter:
                query["price"] = price_filter
            
            cursor = collection.find(query).sort("created_at", -1).skip(skip).limit(limit)
            products_data = await cursor.to_list(length=limit)
            
            products = [ProductDB.from_dict(data) for data in products_data]
            self.logger.info(f"Found {len(products)} products")
            
            return products
            
        except Exception as e:
            self.logger.error(f"Error listing products: {e}")
            raise
    async def count_products(
        self, 
        search_query: Optional[str] = None, 
        tags: Optional[List[str]] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None
    ) -> int:
        try:
            collection = await self._get_collection()
            
            query = {}
            
            if search_query:
                query["$or"] = [
                    {"name": {"$regex": search_query, "$options": "i"}},
                    {"description": {"$regex": search_query, "$options": "i"}}
                ]
            
            if tags:
                query["tags"] = {"$in": tags}
            
            price_filter = {}
            if min_price is not None:
                price_filter["$gte"] = min_price
            if max_price is not None:
                price_filter["$lte"] = max_price
            
            if price_filter:
                query["price"] = price_filter
            
            count = await collection.count_documents(query)
            self.logger.debug(f"Counted {count} products")
            
            return count
            
        except Exception as e:
            self.logger.error(f"Error counting products: {e}")
            raise
        
    async def update_product(self, product_id: str, update_data: Dict[str, Any]) -> Optional[ProductDB]:
        try:
            collection = await self._get_collection()
            self.logger.info(f"Updating product: {product_id}")
            
            if "name" in update_data:
                existing_product = await collection.find_one({
                    "name": {"$regex": f"^{update_data['name']}$", "$options": "i"},
                    "_id": {"$ne": product_id}
                })
                
                if existing_product:
                    self.logger.warning(f"Product with name '{update_data['name']}' already exists")
                    return None
            
            update_data["updated_at"] = datetime.utcnow()
            
            result = await collection.update_one(
                {"_id": product_id},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                self.logger.info(f"Product updated successfully: {product_id}")
                return await self.get_product_by_id(product_id)
            else:
                self.logger.info(f"No changes made to product: {product_id}")
                return await self.get_product_by_id(product_id)
                
        except Exception as e:
            self.logger.error(f"Error updating product {product_id}: {e}")
            raise
        
    async def update_product_images(self, product_id: str, images: List[str]) -> bool:
        """
        Update the images array for a product
        """
        try:
            collection = await self._get_collection()
            self.logger.info(f"Updating images for product: {product_id}")
            
            result = await collection.update_one(
                {"_id": product_id},
                {
                    "$set": {
                        "images": images,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count > 0:
                self.logger.info(f"Images updated successfully for product: {product_id}")
                return True
            else:
                # Check if product exists
                product_exists = await collection.find_one({"_id": product_id})
                if product_exists:
                    self.logger.info(f"No images changes made for product: {product_id}")
                else:
                    self.logger.warning(f"Product not found when updating images: {product_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error updating images for product {product_id}: {e}")
            raise
        
    async def delete_product(self, product_id: str) -> bool:
        try:
            collection = await self._get_collection()
            self.logger.info(f"Deleting product: {product_id}")
            
            result = await collection.delete_one({"_id": product_id})
            
            if result.deleted_count > 0:
                self.logger.info(f"Product deleted successfully: {product_id}")
                return True
            else:
                self.logger.info(f"Product not found for deletion: {product_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error deleting product {product_id}: {e}")
            raise

    async def update_inventory(self, product_id: str, new_stock: int) -> Optional[ProductDB]:
        try:
            collection = await self._get_collection()
            self.logger.info(f"Updating inventory for product: {product_id} to stock: {new_stock}")
            
            result = await collection.update_one(
                {"_id": product_id},
                {
                    "$set": {
                        "stock": new_stock,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count > 0:
                self.logger.info(f"Inventory updated successfully for product: {product_id}")
                return await self.get_product_by_id(product_id)
            else:
                self.logger.info(f"No inventory update made for product: {product_id}")
                return await self.get_product_by_id(product_id)
                
        except Exception as e:
            self.logger.error(f"Error updating inventory for product {product_id}: {e}")
            raise

    async def get_products_by_tags(self, tags: List[str], skip: int = 0, limit: int = 20) -> List[ProductDB]:
        try:
            collection = await self._get_collection()
            self.logger.info(f"Fetching products by tags: {tags}")
            
            cursor = collection.find(
                {"tags": {"$in": tags}}
            ).sort("created_at", -1).skip(skip).limit(limit)
            
            products_data = await cursor.to_list(length=limit)
            products = [ProductDB.from_dict(data) for data in products_data]
            
            self.logger.info(f"Found {len(products)} products with tags {tags}")
            return products
            
        except Exception as e:
            self.logger.error(f"Error fetching products by tags: {e}")
            raise

    async def get_popular_tags(self, limit: int = 10) -> List[Dict[str, Any]]:
        try:
            collection = await self._get_collection()
            self.logger.info(f"Fetching {limit} most popular tags")
            
            pipeline = [
                {"$unwind": "$tags"},
                {"$group": {"_id": "$tags", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
                {"$limit": limit},
                {"$project": {"tag": "$_id", "count": 1, "_id": 0}}
            ]
            
            tags = await collection.aggregate(pipeline).to_list(length=limit)
            self.logger.info(f"Found {len(tags)} popular tags")
            
            return tags
            
        except Exception as e:
            self.logger.error(f"Error fetching popular tags: {e}")
            raise