from typing import List, Optional, Dict, Any
from bson import ObjectId
from pymongo import ASCENDING, DESCENDING
from datetime import datetime
import logging

from .base import BaseRepository
from database.database_models import (
    ProductDB,
    ProductCreateDB, 
    ProductUpdateDB, 
    ProductQueryDB,
    InventoryUpdateDB,
    BulkInventoryUpdateItem,
    BulkUpdateResult,
    SortOrder
)

class ProductRepository(BaseRepository):
    
    def __init__(self):
        super().__init__("products")
        self.logger = logging.getLogger(__name__)
    
    async def create_indexes(self) -> None:
        try:
            await self.collection.create_index([("name", ASCENDING)], unique=True)
            await self.collection.create_index([("price", ASCENDING)])
            await self.collection.create_index([("stock", ASCENDING)])
            await self.collection.create_index([("name", "text")])
            await self.collection.create_index([("created_at", DESCENDING)])
            self.logger.info("Product indexes created successfully")
        except Exception as e:
            self.logger.error(f"Failed to create indexes: {e}")
            raise
    
    async def insert(self, product_data: ProductCreateDB) -> str:
        try:
            result = await self.collection.insert_one(product_data.model_dump())
            self.logger.info(f"Product inserted with ID: {result.inserted_id}")
            return str(result.inserted_id)
        except Exception as e:
            self.logger.error(f"Failed to insert product: {e}")
            raise
    
    async def find_by_id(self, product_id: str) -> Optional[ProductDB]:
        try:
            product_doc = await self.collection.find_one({"_id": ObjectId(product_id)})
            return ProductDB(**product_doc) if product_doc else None
        except Exception as e:
            self.logger.error(f"Error finding product by ID {product_id}: {e}")
            return None
    
    async def find_by_name(self, name: str) -> Optional[ProductDB]:
        try:
            product_doc = await self.collection.find_one({"name": name})
            return ProductDB(**product_doc) if product_doc else None
        except Exception as e:
            self.logger.error(f"Error finding product by name {name}: {e}")
            return None
    
    async def update(self, product_id: str, update_data: ProductUpdateDB) -> bool:
        try:
            result = await self.collection.update_one(
                {"_id": ObjectId(product_id)},
                {"$set": update_data.model_dump(exclude_none=True)}
            )
            
            success = result.modified_count > 0
            if success:
                self.logger.info(f"Product {product_id} updated successfully")
            return success
        except Exception as e:
            self.logger.error(f"Error updating product {product_id}: {e}")
            return False
    
    async def delete(self, product_id: str) -> bool:
        try:
            result = await self.collection.delete_one({"_id": ObjectId(product_id)})
            
            success = result.deleted_count > 0
            if success:
                self.logger.info(f"Product {product_id} deleted successfully")
            return success
        except Exception as e:
            self.logger.error(f"Error deleting product {product_id}: {e}")
            return False
    
    async def list(self, query: ProductQueryDB) -> Dict[str, Any]:
        try:
            mongo_query = {}
            
            if query.search_query:
                mongo_query["$text"] = {"$search": query.search_query}
            
            price_filters = {}
            if query.min_price is not None:
                price_filters["$gte"] = query.min_price
            if query.max_price is not None:
                price_filters["$lte"] = query.max_price
            if price_filters:
                mongo_query["price"] = price_filters
            
            if query.min_stock is not None:
                mongo_query["stock"] = {"$gte": query.min_stock}
            
            skip = (query.page - 1) * query.page_size
            
            total = await self.collection.count_documents(mongo_query)
            
            sort_direction = ASCENDING if query.sort_order == SortOrder.ASCENDING else DESCENDING
            
            cursor = self.collection.find(mongo_query).sort(query.sort_by, sort_direction).skip(skip).limit(query.page_size)
            
            products = []
            async for product_doc in cursor:
                products.append(ProductDB(**product_doc))
            
            return {
                "items": products,
                "total": total,
                "page": query.page,
                "page_size": query.page_size,
                "total_pages": (total + query.page_size - 1) // query.page_size
            }
        except Exception as e:
            self.logger.error(f"Error listing products: {e}")
            raise
    
    async def update_inventory(self, product_id: str, inventory_data: InventoryUpdateDB) -> bool:
        update_data = ProductUpdateDB(
            stock=inventory_data.stock,
            updated_at=inventory_data.updated_at
        )
        return await self.update(product_id, update_data)
    
    async def get_low_stock(self, threshold: int = 10) -> List[ProductDB]:
        try:
            cursor = self.collection.find({"stock": {"$lt": threshold}})
            
            products = []
            async for product_doc in cursor:
                products.append(ProductDB(**product_doc))
            
            return products
        except Exception as e:
            self.logger.error(f"Error getting low stock products: {e}")
            raise
    
    async def bulk_update_inventory(self, updates: List[BulkInventoryUpdateItem]) -> BulkUpdateResult:
        bulk_operations = []
        successful_updates = []
        failed_updates = []
        
        for update_item in updates:
            try:
                bulk_operations.append({
                    "update_one": {
                        "filter": {"_id": ObjectId(update_item.product_id)},
                        "update": {
                            "$set": {
                                "stock": update_item.stock,
                                "updated_at": datetime.utcnow()
                            }
                        }
                    }
                })
            except Exception as e:
                failed_updates.append({
                    "product_id": update_item.product_id,
                    "error": str(e)
                })
        
        if not bulk_operations:
            return BulkUpdateResult(failed=failed_updates)
        
        try:
            result = await self.collection.bulk_write(bulk_operations)
            
            for update_item in updates:
                if update_item.product_id not in [f["product_id"] for f in failed_updates]:
                    successful_updates.append(update_item.product_id)
            
            self.logger.info(f"Bulk inventory update: {len(successful_updates)} successful, {len(failed_updates)} failed")
            
            return BulkUpdateResult(
                successful=successful_updates,
                failed=failed_updates,
                matched_count=result.matched_count,
                modified_count=result.modified_count
            )
            
        except Exception as e:
            self.logger.error(f"Bulk inventory update failed: {e}")
            return BulkUpdateResult(
                failed=[{"error": str(e)}],
                matched_count=0,
                modified_count=0
            )