import logging
from fastapi import APIRouter, Request, Depends, Header, status
from typing import Dict
from services.token_service import TokenService
from services.password_service import PasswordService
from services.auth_service import AuthService
from database import pydantic_models
from decorators.auth_routes_decorators import AuthErrorDecorators
from repository.user_repository import UserRepository
from database.connection import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

logger = logging.getLogger(__name__)

router = APIRouter(tags=['auth'])

# Dependency injection functions
def get_token_service() -> TokenService:
    return TokenService()

def get_password_service() -> PasswordService:
    return PasswordService()

async def get_user_repository(db_session: AsyncSession = Depends(get_db)) -> UserRepository:
    return UserRepository(db_session)

async def get_auth_service(
    user_repository: UserRepository = Depends(get_user_repository),
    password_service: PasswordService = Depends(get_password_service),
    token_service: TokenService = Depends(get_token_service),
) -> AuthService:
    return AuthService(
        logger=logger, 
        user_repository=user_repository,
        password_service=password_service,
        token_service=token_service
    )

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
    response_model=pydantic_models.UserResponse,
    status_code=201,
    summary="Register new user"
)
@AuthErrorDecorators.handle_register_errors
async def register_user(
    request: Request,
    register_data: pydantic_models.User,
    auth_service: AuthService = Depends(get_auth_service),
) -> pydantic_models.UserResponse:
    return await auth_service.register_user(request, register_data)

@router.post(
    '/login',
    response_model=Dict[str, str],
    summary="Login user (returns access + refresh tokens)"
)
@AuthErrorDecorators.handle_login_errors
async def login_user(
    request: Request,
    login_data: pydantic_models.LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> Dict[str, str]:
    return await auth_service.login_user(request, login_data)

@router.post(
    '/refresh-token',
    response_model=Dict[str, str],
    summary="Refresh access token using refresh token"
)
@AuthErrorDecorators.handle_token_errors
async def refresh_token(
    request: Request,
    data: pydantic_models.RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> Dict[str, str]:
    return await auth_service.refresh_token(request, data)

@router.post(
    '/logout',
    status_code=204,
    summary="Logout user (revoke refresh token)"
)
@AuthErrorDecorators.handle_logout_errors
async def logout(
    request: Request,
    token: str = Depends(get_token_from_header),
    auth_service: AuthService = Depends(get_auth_service),
) -> None:
    return await auth_service.logout(request, token)

@router.get(
    '/me',
    response_model=pydantic_models.UserResponse,
    summary="Get current user profile"
)
@AuthErrorDecorators.handle_profile_errors
async def get_current_user(
    request: Request,
    token: str = Depends(get_token_from_header),
    auth_service: AuthService = Depends(get_auth_service),
) -> pydantic_models.UserResponse:
    return await auth_service.get_current_user(request, token)


@router.delete(
    '/cleanup-test-data',
    summary="Cleanup test data (for k6 testing)",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=['testing']
)
async def cleanup_test_data(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(text("DELETE FROM users WHERE email LIKE 'test%@test.com'"))
        await db.commit()
    except Exception:
        await db.rollback()
        raise
