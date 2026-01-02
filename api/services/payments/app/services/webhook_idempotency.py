import asyncio
import logging
from typing import Optional
from datetime import datetime, timedelta

class WebhookIdempotencyService:
    
    def __init__(self, redis_cache, logger: logging.Logger = None):
        self.redis = redis_cache
        self.logger = logger or logging.getLogger(__name__)
        self.EVENT_EXPIRY_DAYS = 7
        self.LOCK_TIMEOUT_SECONDS = 30
        if redis_cache:
            self.logger.info("Idempotency service initialized with Redis")
        else:
            self.logger.warning("Idempotency service initialized WITHOUT Redis - idempotency disabled")
    async def is_duplicate_event(self, event_id: str) -> bool:
        if not self.redis:
            self.logger.error("Redis is None in is_duplicate_event!")
            return False
        
        self.logger.info(f"Checking duplicate for event {event_id}, redis type: {type(self.redis)}")
        
        key = f"stripe_webhook:{event_id}"
        try:
            exists = await self.redis.exists(key)
            self.logger.info(f"Redis.exists() result: {exists}")
            return bool(exists)
        except Exception as e:
            self.logger.error(f"Redis.exists() failed: {e}")
        return False
    
    async def acquire_event_lock(self, event_id: str) -> bool:
        lock_key = f"stripe_webhook_lock:{event_id}"
        
        acquired = await self.redis.set(
            lock_key,
            "processing",
            ttl=self.LOCK_TIMEOUT_SECONDS,
            nx=True
        )
        
        if acquired:
            self.logger.debug(f"Acquired lock for event: {event_id}")
        else:
            self.logger.debug(f"Could not acquire lock for event: {event_id}")
        
        return bool(acquired)
    
    async def release_event_lock(self, event_id: str):
        lock_key = f"stripe_webhook_lock:{event_id}"
        await self.redis.delete(lock_key)
        self.logger.debug(f"Released lock for event: {event_id}")
    
    async def mark_event_processed(self, event_id: str, event_type: str):
        key = f"stripe_webhook:{event_id}"
        
        event_data = {
            "event_id": event_id,
            "event_type": event_type,
            "processed_at": datetime.utcnow().isoformat(),
            "status": "processed"
        }
        
        expiry_seconds = self.EVENT_EXPIRY_DAYS * 24 * 3600
        await self.redis.set(key, event_data, ttl=expiry_seconds)
        
        self.logger.debug(f"Marked event as processed: {event_id} ({event_type})")
    
    async def handle_event_with_idempotency(self, event_id: str, event_type: str, processor_func):
        if await self.is_duplicate_event(event_id):
            return {"status": "already_processed", "event_id": event_id}
        
        lock_acquired = await self.acquire_event_lock(event_id)
        if not lock_acquired:
            await asyncio.sleep(0.5)
            if await self.is_duplicate_event(event_id):
                return {"status": "already_processed_by_other", "event_id": event_id}
            
            self.logger.warning(f"Could not process event {event_id}: lock contention")
            return {"status": "lock_contention", "event_id": event_id}
        
        try:
            if await self.is_duplicate_event(event_id):
                self.logger.info(f"Event {event_id} was processed by another instance while waiting for lock")
                return {"status": "already_processed", "event_id": event_id}
            
            self.logger.info(f"Processing webhook event: {event_id} ({event_type})")
            result = await processor_func()
            
            await self.mark_event_processed(event_id, event_type)
            
            return {**result, "idempotency": "processed", "event_id": event_id}
            
        except Exception as e:
            self.logger.error(f"Error processing event {event_id}: {e}")
            raise
        finally:
            await self.release_event_lock(event_id)