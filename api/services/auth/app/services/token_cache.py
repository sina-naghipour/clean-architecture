import json
import hashlib
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class TokenCacheService:
    def __init__(self, redis_manager):
        self.redis = redis_manager
    
    async def blacklist_token(self, token, expires_in=86400):
        try:
            client = await self.redis.get_client()
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            await client.setex(f"blacklist:{token_hash}", expires_in, "1")
            logger.info(f"Token blacklisted: {token_hash[:8]}...")
            return True
        except Exception as e:
            logger.error(f"Failed to blacklist token: {e}")
            return False
    
    async def is_token_blacklisted(self, token):
        try:
            client = await self.redis.get_client()
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            result = await client.exists(f"blacklist:{token_hash}")
            return bool(result)
        except Exception as e:
            logger.error(f"Failed to check token blacklist: {e}")
            return True  # Fail-safe: assume token is blacklisted if we can't check
    
    async def cache_user_profile(self, user_id, user_data, ttl=300):
        try:
            client = await self.redis.get_client()
            cache_key = f"user:{user_id}:profile"
            await client.setex(cache_key, ttl, json.dumps(user_data, default=str))
            logger.info(f"Cached user {user_id} for {ttl}s")
            return True
        except Exception as e:
            logger.error(f"Failed to cache user profile: {e}")
            return False
    
    async def get_cached_profile(self, user_id):
        try:
            client = await self.redis.get_client()
            cache_key = f"user:{user_id}:profile"
            cached = await client.get(cache_key)
            if cached:
                logger.info(f"Cache hit for user {user_id}")
                return json.loads(cached)
            logger.info(f"Cache miss for user {user_id}")
            return None
        except Exception as e:
            logger.error(f"Failed to get cached profile: {e}")
            return None
    
    async def invalidate_user_cache(self, user_id):
        try:
            client = await self.redis.get_client()
            keys = await client.keys(f"user:{user_id}:*")
            if keys:
                await client.delete(*keys)
                logger.info(f"Invalidated {len(keys)} cache entries for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to invalidate cache: {e}")
            return False
    
    async def store_refresh_token(self, user_id, refresh_token, expires_in=604800):
        try:
            client = await self.redis.get_client()
            key = f"user:{user_id}:refresh_token"
            await client.setex(key, expires_in, refresh_token)
            return True
        except Exception as e:
            logger.error(f"Failed to store refresh token: {e}")
            return False
    
    async def get_refresh_token(self, user_id):
        try:
            client = await self.redis.get_client()
            key = f"user:{user_id}:refresh_token"
            return await client.get(key)
        except Exception as e:
            logger.error(f"Failed to get refresh token: {e}")
            return None