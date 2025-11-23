from functools import wraps
from fastapi import Request, Depends, HTTPException, status
from typing import Callable, Any
from services.cart_services import CartService

class CartErrorDecorators:
    
    @staticmethod
    def handle_get_cart_errors(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(
            request: Request,
            user_id: str,
            cart_service: CartService = Depends(),
        ) -> Any:
            try:
                return await func(request, user_id, cart_service)
            except Exception as e:
                return CartErrorDecorators._handle_get_exception(e, request)
        return wrapper
    
    @staticmethod
    def handle_add_item_errors(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(
            request: Request,
            item_data: Any,
            user_id: str,
            cart_service: CartService = Depends(),
        ) -> Any:
            try:
                return await func(request, item_data, user_id, cart_service)
            except Exception as e:
                return CartErrorDecorators._handle_item_exception(e, request)
        return wrapper
    
    @staticmethod
    def handle_update_item_errors(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(
            request: Request,
            user_id: str,
            update_data: Any,
            item_id: str,
            cart_service: CartService = Depends(),
        ) -> Any:
            try:
                return await func(request, user_id, update_data, item_id, cart_service)
            except Exception as e:
                return CartErrorDecorators._handle_item_exception(e, request)
        return wrapper
    
    @staticmethod
    def handle_remove_item_errors(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(
            request: Request,
            user_id: str,
            item_id: str,
            cart_service: CartService = Depends(),
        ) -> Any:
            try:
                return await func(request, user_id, item_id, cart_service)
            except Exception as e:
                return CartErrorDecorators._handle_item_exception(e, request)
        return wrapper

    @staticmethod
    def handle_clear_cart_errors(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(
            request: Request,
            user_id: str,
            cart_service: CartService = Depends(),
        ) -> Any:
            try:
                return await func(request, user_id, cart_service)
            except Exception as e:
                return CartErrorDecorators._handle_cart_exception(e, request)
        return wrapper
    
    @staticmethod
    def handle_list_carts_errors(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(
            request: Request,
            cart_service: CartService = Depends(),
            page: int = 1,
            page_size: int = 20,
        ) -> Any:
            try:
                return await func(request, cart_service, page, page_size)
            except Exception as e:
                return CartErrorDecorators._handle_list_exception(e, request)
        return wrapper
    
    @staticmethod
    def _handle_get_exception(error: Exception, request: Request) -> Any:
        error_str = str(error).lower()
        
        if "not found" in error_str:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cart not found"
            )
        elif "validation" in error_str or "invalid" in error_str:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(error)
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Cart retrieval failed"
            )
    
    @staticmethod
    def _handle_item_exception(error: Exception, request: Request) -> Any:
        error_str = str(error).lower()
        
        if "not found" in error_str:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item not found"
            )
        elif "validation" in error_str or "invalid" in error_str:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(error)
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Item operation failed"
            )
    
    @staticmethod
    def _handle_cart_exception(error: Exception, request: Request) -> Any:
        error_str = str(error).lower()
        
        if "not found" in error_str:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cart not found"
            )
        elif "validation" in error_str or "invalid" in error_str:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(error)
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Cart operation failed"
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
                detail="Carts listing failed"
            )
