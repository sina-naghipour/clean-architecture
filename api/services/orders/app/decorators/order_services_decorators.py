from functools import wraps
from typing import Callable, Any
from fastapi import Request
from fastapi.responses import JSONResponse
from uuid import UUID
from services.order_helpers import create_problem_response

class OrderServiceDecorators:
    
    @staticmethod
    def handle_create_order_errors(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(self, request: Request, order_data, user_id: str, *args, **kwargs) -> Any:
            try:
                return await func(self, request, order_data, user_id, *args, **kwargs)
            except Exception as e:
                self.logger.error(f"Create order error: {e}")
                return create_problem_response(
                    status_code=500,
                    error_type="internal-error",
                    title="Internal Server Error",
                    detail="Failed to create order",
                    instance=str(request.url)
                )
        return wrapper
    
    @staticmethod
    def handle_get_order_errors(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(self, request: Request, order_id: str, user_id: str, *args, **kwargs) -> Any:
            try:
                order_uuid = UUID(order_id)
            except ValueError:
                return create_problem_response(
                    status_code=400,
                    error_type="bad-request",
                    title="Bad Request",
                    detail="Invalid order ID format",
                    instance=str(request.url)
                )
            
            try:
                return await func(self, request, order_uuid, user_id, *args, **kwargs)
            except Exception as e:
                self.logger.error(f"Get order error: {e}")
                return create_problem_response(
                    status_code=500,
                    error_type="internal-error",
                    title="Internal Server Error",
                    detail="Failed to fetch order",
                    instance=str(request.url)
                )
        return wrapper
    
    @staticmethod
    def handle_list_orders_errors(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(self, request: Request, user_id: str, query_params, *args, **kwargs) -> Any:
            try:
                return await func(self, request, user_id, query_params, *args, **kwargs)
            except Exception as e:
                self.logger.error(f"List orders error: {e}")
                return create_problem_response(
                    status_code=500,
                    error_type="internal-error",
                    title="Internal Server Error",
                    detail="Failed to list orders",
                    instance=str(request.url)
                )
        return wrapper
    
    @staticmethod
    def validate_order_ownership(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(self, request: Request, order_uuid: UUID, user_id: str, *args, **kwargs) -> Any:
            try:
                order_db = await self.order_repo.get_order_by_id(order_uuid)
            except Exception as e:
                self.logger.error(f"Failed to fetch order: {e}")
                return create_problem_response(
                    status_code=500,
                    error_type="internal-error",
                    title="Internal Server Error",
                    detail="Failed to fetch order",
                    instance=str(request.url)
                )
            
            if not order_db:
                return create_problem_response(
                    status_code=404,
                    error_type="not-found",
                    title="Not Found",
                    detail="Order not found",
                    instance=str(request.url)
                )
            
            if order_db.user_id != user_id:
                return create_problem_response(
                    status_code=404,
                    error_type="not-found",
                    title="Not Found",
                    detail="Order not found",
                    instance=str(request.url)
                )
            
            return await func(self, request, order_uuid, user_id, order_db, *args, **kwargs)
        return wrapper