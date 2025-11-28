from typing import List, Optional, Dict, Any
from pymongo.collection import Collection
from pymongo.results import InsertOneResult, UpdateResult, DeleteResult
from bson import ObjectId
import logging
from datetime import datetime

from database.database_models import ProductDB
from database.connection import get_products_collection

logger = logging.getLogger(__name__)

class ProductRepository:
    def __init__(self, collection: Collection = None):
        if collection is not None:
            self.collection = collection
        else:
            self.collection = get_products_collection()
        self.logger = logger.getChild("ProductRepository")

    def create_product(self, product_data: ProductDB) -> Optional[ProductDB]:
        try:
            self.logger.info(f"Creating product: {product_data.name}")
            
            existing_product = self.collection.find_one({
                "name": {"$regex": f"^{product_data.name}$", "$options": "i"}
            })
            
            if existing_product:
                self.logger.warning(f"Product with name '{product_data.name}' already exists")
                return None
            
            product_dict = product_data.to_dict()
            result: InsertOneResult = self.collection.insert_one(product_dict)
            
            if result.inserted_id:
                self.logger.info(f"Product created successfully with ID: {product_data.id}")
                return product_data
            else:
                self.logger.error("Failed to create product")
                return None
                
        except Exception as e:
            self.logger.error(f"Error creating product: {e}")
            raise

    def get_product_by_id(self, product_id: str) -> Optional[ProductDB]:
        try:
            self.logger.info(f"Fetching product by ID: {product_id}")
            
            product_data = self.collection.find_one({"_id": product_id})
            
            if product_data:
                self.logger.info(f"Product found: {product_id}")
                return ProductDB.from_dict(product_data)
            else:
                self.logger.info(f"Product not found: {product_id}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error fetching product {product_id}: {e}")
            raise

    def get_product_by_name(self, name: str) -> Optional[ProductDB]:
        try:
            self.logger.info(f"Fetching product by name: {name}")
            
            product_data = self.collection.find_one({
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

    def list_products(
        self, 
        skip: int = 0, 
        limit: int = 20,
        search_query: Optional[str] = None
    ) -> List[ProductDB]:
        try:
            self.logger.info(f"Listing products - skip: {skip}, limit: {limit}, search: {search_query}")
            
            query = {}
            if search_query:
                query["$or"] = [
                    {"name": {"$regex": search_query, "$options": "i"}},
                    {"description": {"$regex": search_query, "$options": "i"}}
                ]
            
            cursor = self.collection.find(query).sort("created_at", -1).skip(skip).limit(limit)
            products_data = list(cursor)
            
            products = [ProductDB.from_dict(data) for data in products_data]
            self.logger.info(f"Found {len(products)} products")
            
            return products
            
        except Exception as e:
            self.logger.error(f"Error listing products: {e}")
            raise

    def count_products(self, search_query: Optional[str] = None) -> int:
        try:
            query = {}
            if search_query:
                query["$or"] = [
                    {"name": {"$regex": search_query, "$options": "i"}},
                    {"description": {"$regex": search_query, "$options": "i"}}
                ]
            
            count = self.collection.count_documents(query)
            self.logger.debug(f"Counted {count} products")
            
            return count
            
        except Exception as e:
            self.logger.error(f"Error counting products: {e}")
            raise

    def update_product(self, product_id: str, update_data: Dict[str, Any]) -> Optional[ProductDB]:
        try:
            self.logger.info(f"Updating product: {product_id}")
            
            if "name" in update_data:
                existing_product = self.collection.find_one({
                    "name": {"$regex": f"^{update_data['name']}$", "$options": "i"},
                    "_id": {"$ne": product_id}
                })
                
                if existing_product:
                    self.logger.warning(f"Product with name '{update_data['name']}' already exists")
                    return None
            
            update_data["updated_at"] = datetime.utcnow()
            
            result: UpdateResult = self.collection.update_one(
                {"_id": product_id},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                self.logger.info(f"Product updated successfully: {product_id}")
                return self.get_product_by_id(product_id)
            else:
                self.logger.info(f"No changes made to product: {product_id}")
                return self.get_product_by_id(product_id)
                
        except Exception as e:
            self.logger.error(f"Error updating product {product_id}: {e}")
            raise

    def patch_product(self, product_id: str, patch_data: Dict[str, Any]) -> Optional[ProductDB]:
        try:
            self.logger.info(f"Patching product: {product_id}")
            
            if "name" in patch_data:
                existing_product = self.collection.find_one({
                    "name": {"$regex": f"^{patch_data['name']}$", "$options": "i"},
                    "_id": {"$ne": product_id}
                })
                
                if existing_product:
                    self.logger.warning(f"Product with name '{patch_data['name']}' already exists")
                    return None
            
            patch_data["updated_at"] = datetime.utcnow()
            
            result: UpdateResult = self.collection.update_one(
                {"_id": product_id},
                {"$set": patch_data}
            )
            
            if result.modified_count > 0:
                self.logger.info(f"Product patched successfully: {product_id}")
                return self.get_product_by_id(product_id)
            else:
                self.logger.info(f"No changes made to product: {product_id}")
                return self.get_product_by_id(product_id)
                
        except Exception as e:
            self.logger.error(f"Error patching product {product_id}: {e}")
            raise

    def delete_product(self, product_id: str) -> bool:
        try:
            self.logger.info(f"Deleting product: {product_id}")
            
            result: DeleteResult = self.collection.delete_one({"_id": product_id})
            
            if result.deleted_count > 0:
                self.logger.info(f"Product deleted successfully: {product_id}")
                return True
            else:
                self.logger.info(f"Product not found for deletion: {product_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error deleting product {product_id}: {e}")
            raise

    def update_inventory(self, product_id: str, new_stock: int) -> Optional[ProductDB]:
        try:
            self.logger.info(f"Updating inventory for product: {product_id} to stock: {new_stock}")
            
            result: UpdateResult = self.collection.update_one(
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
                return self.get_product_by_id(product_id)
            else:
                self.logger.info(f"No inventory update made for product: {product_id}")
                return self.get_product_by_id(product_id)
                
        except Exception as e:
            self.logger.error(f"Error updating inventory for product {product_id}: {e}")
            raise