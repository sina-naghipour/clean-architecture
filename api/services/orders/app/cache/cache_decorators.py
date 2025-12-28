from functools import wraps
from typing import Callable, Any
import logging
from datetime import datetime
from .cache_service import cache_service

def cache_order(func: Callable) -> Callable:
    @wraps(func)
    async def wrapper(self, order_id, *args, **kwargs):
        if cache_service.enabled:
            cached = await cache_service.get_order(str(order_id))
            if cached:
                self.logger.info(f"Cache hit for order {order_id}")
                return cached
            else:
                self.logger.info(f"Cache miss for order {order_id}")
        
        result = await func(self, order_id, *args, **kwargs)
        
        if result and cache_service.enabled:
            # ALWAYS convert to dict before caching
            if isinstance(result, dict):
                order_dict = result
            elif hasattr(result, 'to_dict'):
                order_dict = result.to_dict()
            elif hasattr(result, '__dict__'):
                # Extract from SQLAlchemy model
                order_dict = {}
                for key, value in result.__dict__.items():
                    if key.startswith('_'):
                        continue
                    # Handle special cases
                    if key == 'id' and hasattr(value, '__str__'):
                        order_dict[key] = str(value)
                    elif key == 'status' and hasattr(value, 'value'):
                        order_dict[key] = value.value
                    else:
                        order_dict[key] = value
            else:
                # Last resort - try to convert
                order_dict = dict(result)
            
            # Ensure critical fields are present
            if 'id' in order_dict and not isinstance(order_dict['id'], str):
                order_dict['id'] = str(order_dict['id'])
            
            if 'status' in order_dict and hasattr(order_dict['status'], 'value'):
                order_dict['status'] = order_dict['status'].value
            
            # Add user_id if missing but available on result object
            if 'user_id' not in order_dict and hasattr(result, 'user_id'):
                order_dict['user_id'] = result.user_id
            
            await cache_service.set_order(str(order_id), order_dict)
        
        return result
    return wrapper

def cache_user_orders(func: Callable) -> Callable:
    @wraps(func)
    async def wrapper(self, user_id: str, skip: int, limit: int, *args, **kwargs):
        page = (skip // limit) + 1 if limit > 0 else 1
        
        if cache_service.enabled:
            cached = await cache_service.get_user_orders(user_id, page, limit)
            if cached:
                self.logger.debug(f"Cache hit for user {user_id} orders page {page}")
                return cached.get('orders', [])
        
        result = await func(self, user_id, skip, limit, *args, **kwargs)
        
        if result and cache_service.enabled:
            cache_data = {
                'orders': result,
                '_cached_at': datetime.utcnow().isoformat()
            }
            await cache_service.set_user_orders(user_id, page, limit, cache_data)
        
        return result
    return wrapper

def invalidate_order_cache(func: Callable) -> Callable:
    @wraps(func)
    async def wrapper(self, order_id, *args, **kwargs):
        result = await func(self, order_id, *args, **kwargs)
        
        if result and cache_service.enabled:
            order_id_str = str(order_id)
            
            cached_order = await cache_service.get_order(order_id_str)
            user_id = cached_order.get('user_id') if cached_order else None
            
            await cache_service.delete_order(order_id_str)
            
            if user_id:
                await cache_service.delete_user_orders(user_id)
        
        return result
    return wrapper