from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection
from database.connection import MongoDBConnection
import logging

class BaseRepository(ABC):    
    def __init__(self, collection_name: str):
        self.collection_name = collection_name
        self._collection: Optional[AsyncIOMotorCollection] = None
        self.logger = logging.getLogger(__name__)
    
    @property
    def collection(self) -> AsyncIOMotorCollection:
        if self._collection is None:
            database = MongoDBConnection.get_database()
            self._collection = database[self.collection_name]
        return self._collection
    
    async def ping(self) -> bool:
        try:
            await self.collection.database.client.admin.command('ping')
            return True
        except Exception as e:
            self.logger.error(f"Database ping failed: {e}")
            return False
    
    async def count_documents(self, query: Dict[str, Any] = None) -> int:
        if query is None:
            query = {}
        return await self.collection.count_documents(query)
    
    async def exists(self, document_id: str) -> bool:
        try:
            result = await self.collection.find_one({"_id": ObjectId(document_id)})
            return result is not None
        except Exception:
            return False