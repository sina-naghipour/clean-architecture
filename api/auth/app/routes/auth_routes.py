import logging
from fastapi import APIRouter, Request, Depends, Header
from typing import Dict
from authentication.tools import PasswordTools, TokenTools
from services.auth_services import AuthService
from services.error_handler import ErrorHandler
from database import models

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/auth', tags=['auth'])

def get_token_tools() -> TokenTools:
    return TokenTools()

def get_password_tools() -> PasswordTools:
    return PasswordTools()

def get_auth_service() -> AuthService:
    return AuthService(logger=logger)

def get_error_handler() -> ErrorHandler:
    return ErrorHandler(logger=logger)

async def get_token_from_header(authorization: str = Header(None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header"
        )
    return authorization[7:]

@router.post(
    '/register',
    response_model=models.UserResponse,
    status_code=201,
    summary="Register new user"
)
async def register_user(
    request: Request,
    register_data: models.RegisterRequest,
    password_tools: PasswordTools = Depends(get_password_tools),
    auth_service: AuthService = Depends(get_auth_service),
    error_handler: ErrorHandler = Depends(get_error_handler)
) -> models.UserResponse:
    try:
        return await auth_service.register_user(request, register_data, password_tools)
    except Exception as e:
        return error_handler.handle_register_error(e, request)

@router.post(
    '/login',
    response_model=Dict[str, str],
    summary="Login user (returns access + refresh tokens)"
)
async def login_user(
    request: Request,
    login_data: models.LoginRequest,
    password_tools: PasswordTools = Depends(get_password_tools),
    token_tools: TokenTools = Depends(get_token_tools),
    auth_service: AuthService = Depends(get_auth_service),
    error_handler: ErrorHandler = Depends(get_error_handler)
) -> Dict[str, str]:
    try:
        return await auth_service.login_user(request, login_data, password_tools, token_tools)
    except Exception as e:
        return error_handler.handle_login_error(e, request)

@router.post(
    '/refresh-token',
    response_model=Dict[str, str],
    summary="Refresh access token using refresh token"
)
async def refresh_token(
    request: Request,
    refresh_data: models.RefreshTokenRequest,
    token_tools: TokenTools = Depends(get_token_tools),
    auth_service: AuthService = Depends(get_auth_service),
    error_handler: ErrorHandler = Depends(get_error_handler)
) -> Dict[str, str]:
    try:
        return await auth_service.refresh_token(request, refresh_data, token_tools)
    except Exception as e:
        return error_handler.handle_token_error(e, request)

@router.post(
    '/logout',
    status_code=204,
    summary="Logout user (revoke refresh token)"
)
async def logout(
    request: Request,
    token: str = Depends(get_token_from_header),
    token_tools: TokenTools = Depends(get_token_tools),
    auth_service: AuthService = Depends(get_auth_service),
    error_handler: ErrorHandler = Depends(get_error_handler)
) -> None:
    try:
        return await auth_service.logout(request, token, token_tools)
    except Exception as e:
        return error_handler.handle_token_error(e, request)

@router.get(
    '/me',
    response_model=models.UserResponse,
    summary="Get current user profile"
)
async def get_current_user(
    request: Request,
    token: str = Depends(get_token_from_header),
    token_tools: TokenTools = Depends(get_token_tools),
    auth_service: AuthService = Depends(get_auth_service),
    error_handler: ErrorHandler = Depends(get_error_handler)
) -> models.UserResponse:
    try:
        return await auth_service.get_current_user(request, token, token_tools)
    except Exception as e:
        return error_handler.handle_profile_error(e, request)