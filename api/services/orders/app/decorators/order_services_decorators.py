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
                result = await func(self, request, order_data, user_id, *args, **kwargs)
                if isinstance(result, JSONResponse) and result.status_code >= 400:
                    return result
                return result
            except Exception as e:
                self.logger.error(f"Create order error: {e}")
                error_detail = str(e)
                if "Payment processing error" in error_detail or "circuit breaker" in error_detail.lower() or "service unavailable" in error_detail.lower():
                    return create_problem_response(
                        status_code=503,
                        error_type="service-unavailable",
                        title="Payment Service Unavailable",
                        detail=error_detail,
                        instance=str(request.url)
                    )
                elif "Order creation failed" in error_detail:
                    return create_problem_response(
                        status_code=400,
                        error_type="bad-request",
                        title="Order Creation Failed",
                        detail=error_detail,
                        instance=str(request.url)
                    )
                else:
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
                order_data = await self.order_repo.get_order_by_id(order_uuid)
            except Exception as e:
                self.logger.error(f"Failed to fetch order: {e}")
                return create_problem_response(
                    status_code=500,
                    error_type="internal-error",
                    title="Internal Server Error",
                    detail="Failed to fetch order",
                    instance=str(request.url)
                )
            
            if not order_data:
                return create_problem_response(
                    status_code=404,
                    error_type="not-found",
                    title="Not Found",
                    detail="Order not found",
                    instance=str(request.url)
                )
            
            # Get user_id from order data (handles both OrderDB objects and dictionaries)
            order_user_id = None
            if isinstance(order_data, dict):
                order_user_id = order_data.get('user_id')
            elif hasattr(order_data, 'user_id'):
                order_user_id = order_data.user_id
            
            self.logger.debug(f"Order type: {type(order_data)}, Request user: {user_id}, Order user: {order_user_id}")
            
            if not order_user_id or order_user_id != user_id:
                return create_problem_response(
                    status_code=404,
                    error_type="not-found",
                    title="Not Found",
                    detail="Order not found",
                    instance=str(request.url)
                )
            
            return await func(self, request, order_uuid, user_id, order_data, *args, **kwargs)
        return wrapper

    @staticmethod
    def handle_payment_webhook_errors(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(self, request: Request, payment_data: dict, *args, **kwargs) -> Any:
            try:
                return await func(self, request, payment_data, *args, **kwargs)
            except Exception as e:
                self.logger.error(f"Payment webhook error: {e}")
                
                if "missing order_id" in str(e).lower() or "missing status" in str(e).lower():
                    return create_problem_response(
                        status_code=400,
                        error_type="bad-request",
                        title="Bad Request",
                        detail=str(e),
                        instance=str(request.url)
                    )
                elif "order not found" in str(e).lower():
                    return create_problem_response(
                        status_code=404,
                        error_type="not-found",
                        title="Not Found",
                        detail=str(e),
                        instance=str(request.url)
                    )
                elif "unknown status" in str(e).lower():
                    return create_problem_response(
                        status_code=400,
                        error_type="bad-request",
                        title="Bad Request",
                        detail=str(e),
                        instance=str(request.url)
                    )
                else:
                    return create_problem_response(
                        status_code=500,
                        error_type="internal-error",
                        title="Internal Server Error",
                        detail="Payment webhook processing failed",
                        instance=str(request.url)
                    )
        return wrapper