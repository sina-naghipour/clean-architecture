from functools import wraps
from typing import Callable, Any
import logging
from datetime import datetime
from .cache_service import cache_service
from database.database_models import OrderDB, OrderStatus

def cache_order(func: Callable) -> Callable:
    @wraps(func)
    async def wrapper(self, order_id, *args, **kwargs):
        order_id_str = str(order_id)
        
        if cache_service.enabled:
            cached = await cache_service.get_order(order_id_str)
            if cached:
                self.logger.info(f"Cache found for order {order_id_str}, user_id: {cached.get('user_id')}, all keys: {list(cached.keys())}")
                if cached.get('user_id') is None:
                    self.logger.error(f"Cache MISSING user_id for order {order_id_str}")
                    await cache_service.delete_order(order_id_str)
                else:
                    cached['status'] = OrderStatus(cached['status'])
                    order_obj = OrderDB.from_dict(cached)
                    self.logger.info(f"Cache hit - order_obj type: {type(order_obj)}")
                    self.logger.info(f"Cache hit - order_obj.user_id: {order_obj.user_id} (type: {type(order_obj.user_id)})")
                    self.logger.info(f"Cache hit - order_obj.id: {order_obj.id} (type: {type(order_obj.id)})")
                    self.logger.info(f"Cache hit - order_obj.to_dict() keys: {list(order_obj.to_dict().keys())}")
                    return order_obj
            self.logger.info(f"Cache miss for order {order_id_str}")
        
        result = await func(self, order_id, *args, **kwargs)
        self.logger.info(f"DB result for order {order_id_str}: {type(result)}")
        
        if result and cache_service.enabled:
            if hasattr(result, 'to_dict'):
                order_dict = result.to_dict()
                self.logger.info(f"to_dict() keys: {list(order_dict.keys())}")
            elif isinstance(result, dict):
                order_dict = result
                self.logger.info(f"dict result keys: {list(order_dict.keys())}")
            else:
                order_dict = {}
                for key, value in result.__dict__.items():
                    if not key.startswith('_'):
                        order_dict[key] = value
                self.logger.info(f"__dict__ keys: {list(order_dict.keys())}")
            
            if 'user_id' in order_dict:
                self.logger.info(f"user_id from order_dict: {order_dict['user_id']}")
            elif hasattr(result, 'user_id'):
                user_id_val = result.user_id
                order_dict['user_id'] = str(user_id_val)
                self.logger.info(f"user_id from result.user_id: {user_id_val}")
            else:
                self.logger.error(f"NO USER_ID FOUND for order {order_id_str}")
            
            order_dict['id'] = str(order_dict.get('id', order_id))
            
            if 'status' in order_dict:
                if hasattr(order_dict['status'], 'value'):
                    order_dict['status'] = order_dict['status'].value
                self.logger.info(f"Caching status: {order_dict['status']}")
            
            self.logger.info(f"Final cache data for {order_id_str}: {list(order_dict.keys())}")
            await cache_service.set_order(order_id_str, order_dict)
        
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
            
            await cache_service.delete_order(order_id_str)
            
            user_id = None
            
            if hasattr(result, 'user_id'):
                user_id = result.user_id
            elif isinstance(result, dict) and result.get('user_id'):
                user_id = result['user_id']
            
            if not user_id:
                try:
                    order_from_db = await self.get_order_by_id(order_id)
                    if order_from_db and hasattr(order_from_db, 'user_id'):
                        user_id = order_from_db.user_id
                except:
                    pass
            
            if user_id:
                await cache_service.delete_user_orders(str(user_id))
        
        return result
    return wrapper