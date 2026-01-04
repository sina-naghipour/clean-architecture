from functools import wraps
from fastapi import Request, Depends, HTTPException, status
from typing import Callable, Any
from services.auth_service import AuthService
import logging

logger = logging.Logger(__name__)
class AuthErrorDecorators:
    
    @staticmethod
    def handle_register_errors(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(
            request: Request,
            register_data: Any,
            auth_service: AuthService,
            *args, **kwargs
        ) -> Any:
            try:
                return await func(request, register_data, auth_service, *args, **kwargs)
            except Exception as e:
                logger.info(f"error_str issssssssss : {e}")
                print(f"error_str issssssssss : {e}")
                logger.debug(f"error_str issssssssss : {e}")
                AuthErrorDecorators._handle_register_exception(e, request)
        return wrapper
    
    @staticmethod
    def handle_login_errors(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(
            request: Request,
            login_data: Any,
            auth_service: AuthService,
            *args, **kwargs
        ) -> Any:
            try:
                return await func(request, login_data, auth_service, *args, **kwargs)
            except Exception as e:
                AuthErrorDecorators._handle_login_exception(e, request)
        return wrapper
    
    @staticmethod
    def handle_token_errors(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(
            auth_service: AuthService,
            request: Request,
            data: Any = None,
            *args, **kwargs
        ) -> Any:
            try:
                return await func(request, data, auth_service, *args, **kwargs)
            except Exception as e:
                AuthErrorDecorators._handle_token_exception(e, request)
        return wrapper
    
    @staticmethod
    def handle_profile_errors(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(
            request: Request,
            token: str,
            auth_service: AuthService,
            *args, **kwargs
        ) -> Any:
            try:
                return await func(request, token, auth_service, *args, **kwargs)
            except Exception as e:
                AuthErrorDecorators._handle_profile_exception(e, request)
        return wrapper
    
    @staticmethod
    def handle_logout_errors(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(
            request: Request,
            token: str,
            auth_service: AuthService,
            *args, **kwargs
        ) -> Any:
            try:
                return await func(request, token, auth_service, *args, **kwargs)
            except Exception as e:
                AuthErrorDecorators._handle_logout_exception(e, request)
        return wrapper
    
    @staticmethod
    def _handle_register_exception(error: Exception, request: Request) -> None:
        error_str = str(error).lower()
        if "duplicate" in error_str or "already exists" in error_str:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User already exists"
            )
        elif "validation" in error_str or "invalid" in error_str:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(error)
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Registration failed"
            )
    
    @staticmethod
    def _handle_login_exception(error: Exception, request: Request) -> None:
        error_str = str(error).lower()
        
        if "invalid" in error_str or "incorrect" in error_str or "not found" in error_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        elif "validation" in error_str:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(error)
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Login failed"
            )
    
    @staticmethod
    def _handle_token_exception(error: Exception, request: Request) -> None:
        error_str = str(error).lower()
        
        if "invalid" in error_str or "expired" in error_str or "signature" in error_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
        elif "missing" in error_str or "empty" in error_str:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing token"
            )
        elif "validation" in error_str:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(error)
            )
        elif "refresh" in error_str:
            if "invalid" in error_str or "expired" in error_str:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired refresh token"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid refresh token"
                )
        else:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Token error: {error}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token request"
            )
            
    @staticmethod
    def _handle_profile_exception(error: Exception, request: Request) -> None:
        error_str = str(error).lower()
        
        if "invalid" in error_str or "expired" in error_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
        elif "not found" in error_str:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Profile retrieval failed"
            )
    
    @staticmethod
    def _handle_logout_exception(error: Exception, request: Request) -> None:
        error_str = str(error).lower()
        
        if "invalid" in error_str or "expired" in error_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
        elif "missing" in error_str:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing token"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Logout failed"
            )