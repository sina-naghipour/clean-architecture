import hashlib
import json
from typing import Optional, Any, Dict
import logging
from datetime import datetime
import os
from .redis_client import redis_client
from dotenv import load_dotenv

load_dotenv()

class CacheService:
    def __init__(self, logger: logging.Logger = None):
        self.logger = logger or logging.getLogger(__name__)
        self.default_ttl = int(os.getenv('CACHE_TTL', '300'))
        self.enabled = os.getenv('CACHE_ENABLED', 'true').lower() == 'true'
    
    def _generate_key(self, prefix: str, *args) -> str:
        key_string = f"{prefix}:{':'.join(str(arg) for arg in args)}"
        return f"orders:{hashlib.md5(key_string.encode()).hexdigest()[:12]}"
    
    def _serialize_for_json(self, data: Any) -> Any:
        """Recursively serialize data for JSON, converting datetime to ISO string"""
        if isinstance(data, dict):
            return {k: self._serialize_for_json(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._serialize_for_json(item) for item in data]
        elif isinstance(data, datetime):
            return data.isoformat()
        else:
            return data
    
    async def get(self, key: str) -> Optional[Any]:
        if not self.enabled or not redis_client.is_connected:
            return None
        
        try:
            client = await redis_client.get_client()
            value = await client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            self.logger.warning(f"Cache get failed for key {key}: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        if not self.enabled or not redis_client.is_connected:
            return False
        
        try:
            client = await redis_client.get_client()
            ttl_seconds = ttl if ttl is not None else self.default_ttl
            
            # Serialize data for JSON
            serialized_data = self._serialize_for_json(value)
            serialized = json.dumps(serialized_data, default=str)
            await client.setex(key, ttl_seconds, serialized)
            return True
        except Exception as e:
            self.logger.warning(f"Cache set failed for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        if not self.enabled or not redis_client.is_connected:
            return False
        
        try:
            client = await redis_client.get_client()
            await client.delete(key)
            return True
        except Exception as e:
            self.logger.warning(f"Cache delete failed for key {key}: {e}")
            return False
    
    async def delete_pattern(self, pattern: str) -> int:
        if not self.enabled or not redis_client.is_connected:
            return 0
        
        try:
            client = await redis_client.get_client()
            keys = await client.keys(pattern)
            if keys:
                await client.delete(*keys)
                return len(keys)
            return 0
        except Exception as e:
            self.logger.warning(f"Cache delete pattern failed for {pattern}: {e}")
            return 0
    
    async def get_order(self, order_id: str) -> Optional[Dict]:
        key = self._generate_key('order', order_id)
        return await self.get(key)
    
    async def set_order(self, order_id: str, order_data: Dict, ttl: Optional[int] = None) -> bool:
        key = self._generate_key('order', order_id)
        data_to_cache = order_data.copy()
        data_to_cache['_cached_at'] = datetime.utcnow().isoformat()
        return await self.set(key, data_to_cache, ttl)
    
    async def delete_order(self, order_id: str) -> bool:
        key = self._generate_key('order', order_id)
        return await self.delete(key)
    
    async def get_user_orders(self, user_id: str, page: int, page_size: int) -> Optional[Dict]:
        key = self._generate_key('user_orders', user_id, page, page_size)
        return await self.get(key)
    
    async def set_user_orders(self, user_id: str, page: int, page_size: int, data: Dict) -> bool:
        key = self._generate_key('user_orders', user_id, page, page_size)
        data_to_cache = data.copy()
        data_to_cache['_cached_at'] = datetime.utcnow().isoformat()
        return await self.set(key, data_to_cache, ttl=60)
    
    async def delete_user_orders(self, user_id: str) -> int:
        pattern = f"orders:*:user_orders:{user_id}:*"
        return await self.delete_pattern(pattern)

cache_service = CacheService()