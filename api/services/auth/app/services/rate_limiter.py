from datetime import datetime

class RateLimiter:
    def __init__(self, redis_manager):
        self.redis_manager = redis_manager
    
    async def check_rate_limit(self, identifier, max_requests=10, window_seconds=60):
        redis = await self.redis_manager.get_connection()
        
        key = f"ratelimit:{identifier}"
        current_time = datetime.now().timestamp()
        window_start = current_time - window_seconds
        
        await redis.zremrangebyscore(key, 0, window_start)
        request_count = await redis.zcard(key)
        
        if request_count >= max_requests:
            oldest = await redis.zrange(key, 0, 0, withscores=True)
            reset_time = oldest[0][1] + window_seconds if oldest else current_time + window_seconds
            
            return {
                "allowed": False,
                "remaining": 0,
                "reset_time": reset_time,
                "retry_after": int(reset_time - current_time)
            }
        
        await redis.zadd(key, {str(current_time): current_time})
        await redis.expire(key, window_seconds)
        
        return {
            "allowed": True,
            "remaining": max_requests - request_count - 1,
            "reset_time": current_time + window_seconds,
            "retry_after": 0
        }