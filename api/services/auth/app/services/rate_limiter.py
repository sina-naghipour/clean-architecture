from datetime import datetime
from functools import wraps
from fastapi import HTTPException, status, Request

class RateLimiter:
    def __init__(self, redis_manager):
        self.redis_manager = redis_manager
    
    async def check_rate_limit(self, identifier, max_requests=10, window_seconds=60):
        redis = await self.redis_manager.get_client()
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
        
    def limit(self, max_requests: int = 5, window_seconds: int = 60, by_ip: bool = False, get_identifier=None):
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                identifier = None
                request = None
                
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break
                
                if not request:
                    for value in kwargs.values():
                        if isinstance(value, Request):
                            request = value
                            break
                
                if get_identifier:
                    identifier = get_identifier(*args, **kwargs)
                elif by_ip and request and hasattr(request, 'client') and request.client:
                    identifier = request.client.host
                else:
                    for arg in args:
                        if hasattr(arg, 'email'):
                            identifier = arg.email
                            break
                    
                    if not identifier:
                        for key, value in kwargs.items():
                            if hasattr(value, 'email'):
                                identifier = value.email
                                break
                
                if identifier:
                    limit_result = await self.check_rate_limit(
                        identifier=identifier,
                        max_requests=max_requests,
                        window_seconds=window_seconds
                    )
                    
                    if not limit_result["allowed"]:
                        raise HTTPException(
                            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                            detail="Too many requests",
                            headers={"Retry-After": str(limit_result["retry_after"])}
                        )
                
                return await func(*args, **kwargs)
            return wrapper
        return decorator