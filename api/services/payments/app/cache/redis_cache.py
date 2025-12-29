import redis.asyncio as redis
import os
import json
from typing import Optional, Any, Union
from functools import wraps
from datetime import timedelta
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class RedisCache:
    _instance = None
    _client = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    async def connect(self):
        if self._client is None:
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
            self._client = redis.from_url(
                redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_keepalive=True
            )
            try:
                await self._client.ping()
                logger.info("Redis connected successfully")
            except Exception as e:
                logger.error(f"Redis connection failed: {e}")
                self._client = None
                raise
    
    async def get(self, key: str) -> Optional[Any]:
        try:
            if self._client is None:
                await self.connect()
            
            value = await self._client.get(key)
            if not value:
                return None
                
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        except Exception as e:
            logger.error(f"Redis get failed for key {key}: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        try:
            if self._client is None:
                await self.connect()
            
            # Handle Pydantic models
            if hasattr(value, 'model_dump'):
                serialized = json.dumps(value.model_dump())
            elif hasattr(value, 'dict'):
                serialized = json.dumps(value.dict())
            elif isinstance(value, (dict, list, tuple, int, float, bool)):
                serialized = json.dumps(value)
            else:
                serialized = json.dumps(str(value))
            
            if ttl:
                await self._client.setex(key, ttl, serialized)
            else:
                await self._client.set(key, serialized)
                
        except Exception as e:
            logger.error(f"Redis set failed for key {key}: {e}")
    
    async def delete(self, key: str):
        try:
            if self._client is None:
                await self.connect()
            
            await self._client.delete(key)
        except Exception as e:
            logger.error(f"Redis delete failed for key {key}: {e}")
    
    async def exists(self, key: str) -> bool:
        try:
            if self._client is None:
                await self.connect()
            
            return await self._client.exists(key) == 1
        except Exception as e:
            logger.error(f"Redis exists failed for key {key}: {e}")
            return False
    
    async def keys(self, pattern: str) -> list:
        try:
            if self._client is None:
                await self.connect()
            
            return await self._client.keys(pattern)
        except Exception as e:
            logger.error(f"Redis keys failed for pattern {pattern}: {e}")
            return []
    
    async def flush_pattern(self, pattern: str):
        try:
            keys = await self.keys(pattern)
            if keys:
                await self._client.delete(*keys)
                logger.info(f"Flushed {len(keys)} keys matching pattern: {pattern}")
        except Exception as e:
            logger.error(f"Redis flush_pattern failed for pattern {pattern}: {e}")
    
    async def close(self):
        if self._client:
            await self._client.close()
            self._client = None

def cache_key(*args, **kwargs) -> str:
    key_parts = []
    
    # Only include simple types that can be stringified
    for arg in args:
        if isinstance(arg, str):
            key_parts.append(arg)
        elif isinstance(arg, (int, float, bool)):
            key_parts.append(str(arg))
        elif hasattr(arg, '__name__'):
            key_parts.append(arg.__name__)
    
    for k, v in sorted(kwargs.items()):
        if isinstance(v, (str, int, float, bool)):
            key_parts.append(f"{k}:{v}")
    
    # Return a simple key without "cache:" prefix
    return "_".join(key_parts)

def cached(ttl: int = 300, key_prefix: str = ""):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            base_key = cache_key(*args, **kwargs)
            cache_key_str = f"cache:{key_prefix}:{func.__name__}:{base_key}" if key_prefix else f"cache:{func.__name__}:{base_key}"
            
            cache = RedisCache()
            
            # Try to get from cache
            cached_value = await cache.get(cache_key_str)
            if cached_value is not None:
                logger.debug(f"Cache hit for key: {cache_key_str}")
                
                # If the function returns a Pydantic model, reconstruct it
                if isinstance(cached_value, dict):
                    try:
                        # Get return type annotation
                        import inspect
                        sig = inspect.signature(func)
                        return_type = sig.return_annotation
                        
                        if return_type != inspect.Signature.empty:
                            # Check if it's a Pydantic model
                            if hasattr(return_type, 'model_validate'):
                                return return_type.model_validate(cached_value)
                            elif hasattr(return_type, 'parse_obj'):
                                return return_type.parse_obj(cached_value)
                    except Exception:
                        pass
                
                return cached_value
            
            # Cache miss - call the actual function
            logger.debug(f"Cache miss for key: {cache_key_str}")
            result = await func(*args, **kwargs)
            
            # Store in cache if result is not None
            if result is not None:
                await cache.set(cache_key_str, result, ttl)
                logger.debug(f"Cache set for key: {cache_key_str} (TTL: {ttl}s)")
            
            return result
        return wrapper
    return decorator

def invalidate_cache(pattern: str = None):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache = RedisCache()
            
            result = await func(*args, **kwargs)
            
            if pattern:
                await cache.flush_pattern(pattern)
                logger.debug(f"Invalidated cache pattern: {pattern}")
            
            return result
        return wrapper
    return decorator