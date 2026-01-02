# services/idempotency_service.py
import json
import logging

logger = logging.getLogger(__name__)

class IdempotencyService:
    def __init__(self, redis_cache):
        logger.info(f"IdempotencyService INIT - Redis: {redis_cache}")
        self.redis = redis_cache
    
    async def execute_once(self, key: str, operation, ttl=86400):
        logger.info(f"========== IDEMPOTENCY START ==========")
        logger.info(f"Key: {key}")
        logger.info(f"Redis exists: {self.redis is not None}")
        logger.info(f"Redis type: {type(self.redis)}")
        
        if self.redis is None:
            logger.warning("REDIS IS NONE - Skipping cache")
            result = await operation()
            logger.info(f"No-Redis result: {result}")
            return result
        
        full_key = f"idemp:{key}"
        logger.info(f"Full Redis key: {full_key}")
        
        try:
            logger.info("Checking Redis cache...")
            cached = await self.redis.get(full_key)
            logger.info(f"Cache check result: {cached}")
            
            if cached:
                logger.info(f"✅ CACHE HIT for {key}")
                parsed = json.loads(cached)
                logger.info(f"Cached value: {parsed}")
                return parsed
            
            logger.info(f"❌ CACHE MISS for {key}")
            logger.info("Executing operation...")
            result = await operation()
            logger.info(f"Operation result: {result}")
            
            logger.info("Storing in Redis...")
            await self.redis.set(full_key, json.dumps(result), ttl)
            logger.info(f"✅ CACHED result for {key}")
            logger.info(f"TTL: {ttl} seconds")
            
            return result
            
        except Exception as e:
            logger.error(f"🔥 REDIS ERROR: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            logger.warning("Falling back to operation without cache")
            result = await operation()
            logger.info(f"Fallback result: {result}")
            return result