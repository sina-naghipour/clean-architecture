from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import os
import logging
from .database_models import ProductDB

logger = logging.getLogger(__name__)

class MongoDBConnection:
    def __init__(self):
        self.client = None
        self.db = None
        self.logger = logger.getChild("MongoDBConnection")
        
    async def connect(self, connection_string: str = None, db_name: str = None):
        try:
            connection_string = connection_string or os.getenv(
                "MONGODB_URI", "mongodb://mongodb:27017/"
            )
            db_name = db_name or os.getenv("MONGODB_DB_NAME", "product_db")
            
            self.logger.info(f"Connecting to MongoDB: {db_name}")
            self.logger.debug(f"Connection string: {self._mask_connection_string(connection_string)}")
            
            self.client = AsyncIOMotorClient(connection_string, serverSelectionTimeoutMS=5000)
            self.db = self.client[db_name]
            
            # Test connection
            await self.client.admin.command('ping')
            self.logger.info("Successfully connected to MongoDB")
            
            await self._setup_indexes()
            
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            self.logger.error(f"MongoDB connection failed: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error during MongoDB connection: {e}")
            raise

    def _mask_connection_string(self, connection_string: str) -> str:
        if "@" in connection_string:
            parts = connection_string.split("@")
            if len(parts) == 2:
                user_pass = parts[0]
                if "://" in user_pass:
                    protocol, credentials = user_pass.split("://", 1)
                    if ":" in credentials:
                        user, _ = credentials.split(":", 1)
                        return f"{protocol}://{user}:****@{parts[1]}"
        return connection_string

    async def _setup_indexes(self):
        try:
            collection = self.db[ProductDB.COLLECTION_NAME]
            indexes = ProductDB.get_indexes()
            
            if indexes:
                # For Motor, we need to handle index creation differently
                for index_spec in indexes:
                    # Handle different index formats
                    if isinstance(index_spec, dict):
                        # If it's already a dict with 'key' and other options
                        keys = index_spec.get('key', [])
                        options = {k: v for k, v in index_spec.items() if k != 'key'}
                        await collection.create_index(keys, **options)
                    elif isinstance(index_spec, (list, tuple)):
                        # If it's a list of (field, direction) pairs
                        await collection.create_index(index_spec)
                    else:
                        self.logger.warning(f"Unsupported index format: {index_spec}")
                
                self.logger.info(f"Database indexes created/verified for collection: {ProductDB.COLLECTION_NAME}")
        except Exception as e:
            self.logger.error(f"Index creation failed: {e}")
            raise

    def get_collection(self, collection_name: str = None):
        if self.db is None:
            self.logger.error("Attempted to get collection without active database connection")
            raise Exception("Database not connected. Call connect() first.")
        
        collection_name = collection_name or ProductDB.COLLECTION_NAME
        self.logger.debug(f"Accessing collection: {collection_name}")
        return self.db[collection_name]

    async def close(self):
        if self.client:
            self.client.close()
            self.logger.info("MongoDB connection closed")
        else:
            self.logger.debug("No active MongoDB connection to close")

db_connection = MongoDBConnection()

async def get_db():
    if db_connection.db is None:
        await db_connection.connect()
    return db_connection.db

async def get_products_collection():
    db = await get_db()
    collection = db[ProductDB.COLLECTION_NAME]
    logger.debug("Products collection retrieved")
    return collection