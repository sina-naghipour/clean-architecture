from functools import wraps
from typing import Callable, Any
from sqlalchemy.exc import SQLAlchemyError
import logging

class OrderRepositoryDecorators:
    
    @staticmethod
    def handle_repository_operation(operation_name: str):
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(self, *args, **kwargs) -> Any:
                self.logger.info(f"Starting {operation_name}")
                
                try:
                    result = await func(self, *args, **kwargs)
                    self.logger.info(f"Completed {operation_name} successfully")
                    return result
                    
                except SQLAlchemyError as e:
                    self.logger.error(f"Database error in {operation_name}: {e}")
                    await self.session.rollback()
                    raise
                    
                except Exception as e:
                    self.logger.error(f"Unexpected error in {operation_name}: {e}", exc_info=True)
                    await self.session.rollback()
                    raise
                    
            return wrapper
        return decorator