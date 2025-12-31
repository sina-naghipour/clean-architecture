import os
import redis.asyncio as redis
import logging

logger = logging.getLogger(__name__)

class RedisManager:
    def __init__(self):
        self.host = os.getenv("REDIS_HOST", "redis")
        self.port = int(os.getenv("REDIS_PORT", 6379))
        self.db = int(os.getenv("REDIS_DB", 0))
        self._client = None
        
    async def get_client(self):
        if not self._client:
            try:
                self._client = redis.Redis(
                    host=self.host,
                    port=self.port,
                    db=self.db,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5
                )
                await self._client.ping()
                logger.info(f"Redis connected to {self.host}:{self.port}")
            except Exception as e:
                logger.error(f"Redis connection failed: {e}")
                self._client = None
        return self._client
    
    async def close(self):
        if self._client:
            await self._client.close()
            self._client = None

redis_manager = RedisManager()