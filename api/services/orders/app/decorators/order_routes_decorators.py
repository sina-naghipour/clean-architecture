from functools import wraps
from fastapi import Request, Depends, HTTPException, status, Header, Body
from typing import Callable, Any
from services.order_services import OrderService
import os
class OrderErrorDecorators:
    
    @staticmethod
    def handle_create_errors(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(
            request: Request,
            order_data: Any,
            order_service: OrderService = Depends(),
        ) -> Any:
            try:
                return await func(request, order_data, order_service)
            except Exception as e:
                return OrderErrorDecorators._handle_create_exception(e, request)
        return wrapper
    
    @staticmethod
    def handle_get_errors(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(
            request: Request,
            order_id: str,
            order_service: OrderService = Depends(),
        ) -> Any:
            try:
                return await func(request, order_id, order_service)
            except Exception as e:
                return OrderErrorDecorators._handle_get_exception(e, request)
        return wrapper
    
    @staticmethod
    def handle_list_errors(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(
            request: Request,
            page: int = 1,
            page_size: int = 20,
            order_service: OrderService = Depends(),
        ) -> Any:
            try:
                return await func(request, page, page_size, order_service)
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
            print(error_str)
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

    @staticmethod
    @staticmethod
    def handle_payment_webhook_errors(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(
            request: Request,
            payment_data: dict = Body(...),
            api_key: str = Header(None, alias="X-API-Key"),
            order_service: OrderService = Depends()
        ) -> Any:
            internal_key = os.getenv("INTERNAL_API_KEY", "default_internal_key")
            
            if not api_key or api_key != internal_key:
                raise HTTPException(
                    status_code=403, 
                    detail="Forbidden: Invalid or missing API key"
                )
            
            try:
                return await order_service.handle_payment_webhook(request, payment_data)
            except Exception as e:
                error_str = str(e).lower()
                
                if "not found" in error_str:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Order not found"
                    )
                elif "missing order_id" in error_str or "missing status" in error_str:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Missing required fields"
                    )
                else:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Payment webhook processing failed"
                    )
        return wrapper
    
    @staticmethod
    def _handle_payment_webhook_exception(error: Exception, request: Request) -> Any:
        error_str = str(error).lower()
        
        if "invalid api key" in error_str or "missing api key" in error_str:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid or missing API key"
            )
        elif "order not found" in error_str:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        elif "missing order_id" in error_str or "missing status" in error_str:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing required fields: order_id and status"
            )
        elif "invalid uuid" in error_str or "badly formed" in error_str:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid UUID format"
            )
        elif "unknown status" in error_str:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unknown payment status"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Payment webhook processing failed"
            )