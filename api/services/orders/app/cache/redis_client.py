import redis.asyncio as redis
from redis.asyncio import ConnectionPool
import os
import json
import logging
from typing import Optional, Any
from dotenv import load_dotenv

load_dotenv()

class RedisClient:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self.logger = logging.getLogger(__name__)
            self._pool = None
            self.is_connected = False
    
    async def get_pool(self) -> ConnectionPool:
        if self._pool is None:
            redis_host = os.getenv('REDIS_HOST', 'localhost')
            redis_port = int(os.getenv('REDIS_PORT', '6379'))
            
            self._pool = ConnectionPool.from_url(
                f"redis://{redis_host}:{redis_port}/1",
                max_connections=int(os.getenv('REDIS_MAX_CONNECTIONS', '20')),
                decode_responses=True,
                socket_connect_timeout=5,
                socket_keepalive=True
            )
            self.is_connected = True
            self.logger.info(f"Redis connection pool created for DB 1")
        return self._pool
    
    async def get_client(self) -> redis.Redis:
        pool = await self.get_pool()
        return redis.Redis(connection_pool=pool)
    
    async def ping(self) -> bool:
        try:
            client = await self.get_client()
            await client.ping()
            return True
        except Exception:
            return False
    
    async def close(self):
        if self._pool:
            await self._pool.disconnect()
            self._pool = None
            self.is_connected = False
            self.logger.info("Redis connection pool closed")

redis_client = RedisClient()