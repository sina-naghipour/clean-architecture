import functools
import hashlib
import json

class CacheDecorators:
    @staticmethod
    def cache_user_profile(ttl=300):
        def decorator(func):
            @functools.wraps(func)
            async def wrapper(self, *args, **kwargs):
                user_id = None
                if len(args) > 1:
                    user_id = args[1]
                elif 'user_id' in kwargs:
                    user_id = kwargs['user_id']
                
                if not user_id:
                    return await func(self, *args, **kwargs)
                
                redis = await self.redis_manager.get_client()
                cache_key = f"user:{user_id}:profile"
                
                cached_data = await redis.get(cache_key)
                if cached_data:
                    self.logger.info(f"Cache hit for user {user_id}")
                    return json.loads(cached_data)
                
                result = await func(self, *args, **kwargs)
                
                if result:
                    await redis.setex(
                        cache_key,
                        ttl,
                        json.dumps(result, default=str)
                    )
                    self.logger.info(f"Cached user {user_id} for {ttl}s")
                
                return result
            return wrapper
        return decorator
    
    @staticmethod
    def invalidate_user_cache(func):
        @functools.wraps(func)
        async def wrapper(self, *args, **kwargs):
            result = await func(self, *args, **kwargs)
            
            user_id = None
            if result and hasattr(result, 'id'):
                user_id = str(result.id)
            elif len(args) > 1:
                user_id = args[1]
            
            if user_id:
                redis = await self.redis_manager.get_client()
                cache_keys = [
                    f"user:{user_id}:profile",
                    f"user:{user_id}:tokens"
                ]
                await redis.delete(*cache_keys)
                self.logger.info(f"Invalidated cache for user {user_id}")
            
            return result
        return wrapper