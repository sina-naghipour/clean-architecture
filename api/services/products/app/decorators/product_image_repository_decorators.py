import logging
from functools import wraps
from typing import Callable, Any, TypeVar, Coroutine
from motor.motor_asyncio import AsyncIOMotorCollection

logger = logging.getLogger(__name__)

C = TypeVar('C', bound=Callable[..., Coroutine[Any, Any, Any]])


def handle_repository_errors(func: C) -> C:
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Repository error in {func.__name__}: {e}", exc_info=True)
            raise
    return wrapper


def ensure_collection(func: C) -> C:
    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        if self.collection is None:
            self.collection = await self._get_collection()
        return await func(self, *args, **kwargs)
    return wrapper


def log_operation(operation_name: str = None):
    def decorator(func: C) -> C:
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            name = operation_name or func.__name__
            self.logger.info(f"Starting {name} with args: {args}, kwargs: {kwargs}")
            try:
                result = await func(self, *args, **kwargs)
                self.logger.info(f"Completed {name} successfully")
                return result
            except Exception as e:
                self.logger.error(f"Failed {name}: {e}")
                raise
        return wrapper
    return decorator


def validate_image_id(func: C) -> C:
    @wraps(func)
    async def wrapper(self, image_id: str, *args, **kwargs):
        print('Image_ID : ', image_id, '*args :', args)
        if not isinstance(image_id, str) or image_id.strip() == "":
            raise ValueError("Invalid image ID")
        return await func(self, image_id, *args, **kwargs)
    return wrapper


def validate_image_id_set_primary_image(func: C) -> C:
    @wraps(func)
    async def wrapper(self, product_id: str, image_id: str, *args, **kwargs):
        print('Image_ID : ', image_id, '*args :', args)
        if not isinstance(image_id, str) or image_id.strip() == "":
            raise ValueError("Invalid image ID")
        return await func(self, product_id, image_id, *args, **kwargs)
    return wrapper


def validate_product_id(func: C) -> C:
    @wraps(func)
    async def wrapper(self, product_id: str, *args, **kwargs):
        if not isinstance(product_id, str) or product_id.strip() == "":
            raise ValueError("Invalid product ID")
        return await func(self, product_id, *args, **kwargs)
    return wrapper

def validate_product_id_set_primary_image(func: C) -> C:
    @wraps(func)
    async def wrapper(self, product_id: str, image_id: str, *args, **kwargs):
        if not isinstance(product_id, str) or product_id.strip() == "":
            raise ValueError("Invalid product ID")
        return await func(self, product_id, image_id, *args, **kwargs)
    return wrapper



def transaction_safe(func: C) -> C:
    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        try:
            return await func(self, *args, **kwargs)
        except Exception as e:
            if hasattr(self, 'session'):
                await self.session.abort_transaction()
            raise
    return wrapper
