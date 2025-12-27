import os
import json
import redis.asyncio as redis
import asyncio
import logging

logger = logging.getLogger(__name__)

class RedisManager:
    def __init__(self):
        self.host = os.getenv("REDIS_HOST", "localhost")
        self.port = int(os.getenv("REDIS_PORT", 6379))
        self.db = int(os.getenv("REDIS_DB", 0))
        self._client = None
        self.connected = False
        
    async def connect(self):
        try:
            self._client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                max_connections=20
            )
            
            await self._client.ping()
            self.connected = True
            logger.info(f"Redis connected to {self.host}:{self.port}")
            return True
            
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            self._client = None
            self.connected = False
            return False
    
    async def get_client(self):
        if not self._client or not self.connected:
            await self.connect()
        return self._client
    
    async def close(self):
        if self._client:
            await self._client.close()
            self._client = None
            self.connected = False
            logger.info("Redis connection closed")

redis_manager = RedisManager()