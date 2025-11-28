from functools import wraps
from fastapi import Request, Depends, HTTPException, status
from typing import Callable, Any
from services.order_services import OrderService

class OrderErrorDecorators:
    
    @staticmethod
    def handle_create_errors(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(
            request: Request,
            order_data: Any,
            user_id: str,
            order_service: OrderService = Depends(),
        ) -> Any:
            try:
                return await func(request, order_data, user_id, order_service)
            except Exception as e:
                return OrderErrorDecorators._handle_create_exception(e, request)
        return wrapper
    
    @staticmethod
    def handle_get_errors(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(
            request: Request,
            order_id: str,
            user_id: str,
            order_service: OrderService = Depends(),
        ) -> Any:
            try:
                return await func(request, order_id, user_id, order_service)
            except Exception as e:
                return OrderErrorDecorators._handle_get_exception(e, request)
        return wrapper
    
    @staticmethod
    def handle_list_errors(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(
            request: Request,
            user_id: str,
            page: int = 1,
            page_size: int = 20,
            order_service: OrderService = Depends(),
        ) -> Any:
            try:
                return await func(request, user_id, page, page_size, order_service)
            except Exception as e:
                return OrderErrorDecorators._handle_list_exception(e, request)
        return wrapper
    
    @staticmethod
    def _handle_create_exception(error: Exception, request: Request) -> Any:
        error_str = str(error).lower()
        
        if "not found" in error_str:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cart or address not found"
            )
        elif "empty" in error_str or "no items" in error_str:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot create order with empty cart"
            )
        elif "validation" in error_str or "invalid" in error_str:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(error)
            )
        elif "conflict" in error_str or "already exists" in error_str:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Order already exists"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Order creation failed"
            )
    
    @staticmethod
    def _handle_get_exception(error: Exception, request: Request) -> Any:
        error_str = str(error).lower()
        if "not found" in error_str:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        elif "validation" in error_str or "invalid" in error_str:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(error)
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Order retrieval failed"
            )
    
    @staticmethod
    def _handle_list_exception(error: Exception, request: Request) -> Any:
        error_str = str(error).lower()
        
        if "validation" in error_str:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(error)
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Orders listing failed"
            )
