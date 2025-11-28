from functools import wraps
from fastapi import Request, Depends, HTTPException, status
from typing import Callable, Any
from services.product_services import ProductService

class ProductErrorDecorators:
    
    @staticmethod
    def handle_create_errors(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(
            request: Request,
            product_data: Any,
            product_service: ProductService = Depends(),
        ) -> Any:
            try:
                return func(request, product_data, product_service)
            except Exception as e:
                return ProductErrorDecorators._handle_create_exception(e, request)
        return wrapper
    
    @staticmethod
    def handle_get_errors(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(
            request: Request,
            product_id: str,
            product_service: ProductService = Depends(),
        ) -> Any:
            try:
                return func(request, product_id, product_service)
            except Exception as e:
                return ProductErrorDecorators._handle_get_exception(e, request)
        return wrapper
    
    @staticmethod
    def handle_list_errors(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(
            request: Request,
            product_service: ProductService = Depends(),
            page: int = 1,
            page_size: int = 20,
            q: str = None,
        ) -> Any:
            try:
                return func(request, product_service, page, page_size, q)
            except Exception as e:
                return ProductErrorDecorators._handle_list_exception(e, request)
        return wrapper
    
    @staticmethod
    def handle_patch_errors(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(
            request: Request,
            product_id: str,
            patch_data: Any,
            product_service: ProductService = Depends(),
        ) -> Any:
            try:
                return func(request, product_id, patch_data, product_service)
            except Exception as e:
                return ProductErrorDecorators._handle_update_exception(e, request)  # Can reuse the same exception handler
        return wrapper
    
    @staticmethod
    def handle_update_errors(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(
            request: Request,
            product_id: str,
            update_data: Any,
            product_service: ProductService = Depends(),
        ) -> Any:
            try:
                return func(request, product_id, update_data, product_service)
            except Exception as e:
                return ProductErrorDecorators._handle_update_exception(e, request)
        return wrapper
    
    @staticmethod
    def handle_delete_errors(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(
            request: Request,
            product_id: str,
            product_service: ProductService = Depends(),
        ) -> Any:
            try:
                return func(request, product_id, product_service)
            except Exception as e:
                return ProductErrorDecorators._handle_delete_exception(e, request)
        return wrapper
    
    @staticmethod
    def handle_inventory_errors(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(
            request: Request,
            product_id: str,
            inventory_data: Any,
            product_service: ProductService = Depends(),
        ) -> Any:
            try:
                return func(request, product_id, inventory_data, product_service)
            except Exception as e:
                return ProductErrorDecorators._handle_inventory_exception(e, request)
        return wrapper
    
    @staticmethod
    def _handle_create_exception(error: Exception, request: Request) -> Any:
        error_str = str(error).lower()
        print('error_str', error_str)
        if "duplicate" in error_str or "already exists" in error_str:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Product already exists"
            )
        elif "validation" in error_str or "invalid" in error_str:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(error)
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Product creation failed"
            )
    
    @staticmethod
    def _handle_get_exception(error: Exception, request: Request) -> Any:
        error_str = str(error).lower()
        
        if "not found" in error_str:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        elif "validation" in error_str or "invalid" in error_str:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(error)
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Product retrieval failed"
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
                detail="Products listing failed"
            )
    
    @staticmethod
    def _handle_update_exception(error: Exception, request: Request) -> Any:
        error_str = str(error).lower()
        
        if "not found" in error_str:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        elif "validation" in error_str or "invalid" in error_str:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(error)
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Product update failed"
            )
    
    @staticmethod
    def _handle_delete_exception(error: Exception, request: Request) -> Any:
        error_str = str(error).lower()
        
        if "not found" in error_str:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        elif "validation" in error_str or "invalid" in error_str:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(error)
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Product deletion failed"
            )
    
    @staticmethod
    def _handle_inventory_exception(error: Exception, request: Request) -> Any:
        error_str = str(error).lower()
        
        if "not found" in error_str:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        elif "validation" in error_str or "invalid" in error_str:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(error)
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Inventory update failed"
            )