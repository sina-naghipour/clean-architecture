from functools import wraps
from fastapi import Request, Depends, HTTPException, status
from typing import Callable, Any
from services.profile_services import ProfileService
from database import models


class ProfileErrorDecorators:
    
    @staticmethod
    def handle_get_errors(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(
            request: Request,
            user_id: str,
            profile_service: ProfileService = Depends(),
        ) -> Any:
            try:
                return await func(request, user_id, profile_service)
            except Exception as e:
                return ProfileErrorDecorators._handle_get_exception(e, request)
        return wrapper
    
    @staticmethod
    def handle_update_errors(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(
            request: Request,
            profile_data: Any,
            user_id: str,
            profile_service: ProfileService = Depends(),
        ) -> Any:
            try:
                return await func(request, profile_data, user_id, profile_service)
            except Exception as e:
                return ProfileErrorDecorators._handle_update_exception(e, request)
        return wrapper
    
    @staticmethod
    def handle_password_errors(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(
            request: Request,
            password_data: Any,
            user_id: str,
            profile_service: ProfileService = Depends(),
        ) -> Any:
            try:
                return await func(request, password_data, user_id, profile_service)
            except Exception as e:
                return ProfileErrorDecorators._handle_password_exception(e, request)
        return wrapper
    
    @staticmethod
    def handle_address_errors(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(
            request: Request,
            address_data: Any,
            user_id: str,
            profile_service: ProfileService = Depends(),
        ) -> Any:
            try:
                return await func(request, address_data, user_id, profile_service)
            except Exception as e:
                return ProfileErrorDecorators._handle_address_exception(e, request)
        return wrapper
    
    @staticmethod
    def handle_address_update_errors(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(
            request: Request,
            address_id: str,
            address_data: models.AddressRequest,
            user_id: str,
            profile_service: ProfileService = Depends(),
        ) -> Any:
            try:
                return await func(request, address_id, address_data, user_id, profile_service)
            except Exception as e:
                return ProfileErrorDecorators._handle_address_operations_exception(e, request)
        return wrapper
    
    @staticmethod
    def handle_address_delete_errors(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(
            request: Request,
            address_id: str,
            user_id: str,
            profile_service: ProfileService = Depends(),
        ) -> Any:
            try:
                return await func(request, address_id, user_id, profile_service)
            except Exception as e:
                return ProfileErrorDecorators._handle_address_operations_exception(e, request)
        return wrapper
    
    @staticmethod
    def _handle_get_exception(error: Exception, request: Request) -> Any:
        error_str = str(error).lower()
        
        if "not found" in error_str:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found"
            )
        elif "validation" in error_str or "invalid" in error_str:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(error)
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Profile retrieval failed"
            )
    
    @staticmethod
    def _handle_update_exception(error: Exception, request: Request) -> Any:
        error_str = str(error).lower()
        
        if "not found" in error_str:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found"
            )
        elif "validation" in error_str or "invalid" in error_str:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(error)
            )
        elif "conflict" in error_str or "already exists" in error_str:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Profile update conflict"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Profile update failed"
            )
    
    @staticmethod
    def _handle_password_exception(error: Exception, request: Request) -> Any:
        error_str = str(error).lower()
        
        if "not found" in error_str:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found"
            )
        elif "invalid password" in error_str or "incorrect password" in error_str:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        elif "validation" in error_str or "invalid" in error_str:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(error)
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Password change failed"
            )
    
    @staticmethod
    def _handle_address_exception(error: Exception, request: Request) -> Any:
        error_str = str(error).lower()
        
        if "validation" in error_str or "invalid" in error_str:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(error)
            )
        elif "conflict" in error_str or "already exists" in error_str:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Address already exists"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Address operation failed"
            )
    
    @staticmethod
    def _handle_address_operations_exception(error: Exception, request: Request) -> Any:
        error_str = str(error).lower()
        
        if "not found" in error_str:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Address not found"
            )
        elif "validation" in error_str or "invalid" in error_str:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(error)
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Address operation failed"
            )
