from .auth_helpers import create_problem_response
from decorators.auth_services_decorators import handle_database_errors, handle_validation_errors
from fastapi import Request
from fastapi.responses import JSONResponse
from typing import Dict
from authentication.tools import PasswordTools, TokenTools
from database import pydantic_models
from repository.user_repository import UserRepository

class AuthService:
    def __init__(self, logger, user_repository: UserRepository):
        self.logger = logger
        self.user_repository = user_repository

    @handle_database_errors
    @handle_validation_errors
    async def register_user(
        self,
        request: Request,
        register_data: pydantic_models.User,
        password_tools: PasswordTools
    ) -> pydantic_models.UserResponse:
        self.logger.info(f"Registration attempt for email: {register_data.email}")
        
        user_exists = await self.user_repository.email_exists(register_data.email)
        
        if user_exists:
            return create_problem_response(
                status_code=409,
                error_type="conflict",
                title="Conflict",
                detail="User with this email already exists",
                instance=str(request.url)
            )
        
        hashed_password = password_tools.encode_password(register_data.password)
        
        user_dict = {
            "email": register_data.email,
            "password": hashed_password,
            "name": register_data.name
        }
        
        user = await self.user_repository.create_user(user_dict)
        
        user_response = pydantic_models.UserResponse(
            id=str(user.id),
            email=user.email,
            name=user.name
        )
        
        self.logger.info(f"User registered successfully: {register_data.email}")
        
        response = JSONResponse(
            status_code=201,
            content=user_response.model_dump(),
            headers={"Location": f"/api/users/{user_response.id}"}
        )
        return response

    @handle_database_errors
    async def login_user(
        self,
        request: Request,
        login_data: pydantic_models.LoginRequest,
        password_tools: PasswordTools,
        token_tools: TokenTools
    ) -> Dict[str, str]:
        self.logger.info(f"Login attempt for email: {login_data.email}")
        
        user = await self.user_repository.get_active_user_by_email(login_data.email)
        
        if not user:
            self.logger.warning(f"Invalid login attempt for email: {login_data.email}")
            return create_problem_response(
                status_code=401,
                error_type="unauthorized",
                title="Unauthorized",
                detail="Invalid email or password",
                instance=str(request.url)
            )
        
        is_password_valid = password_tools.verify_password(login_data.password, user.password)
        
        if not is_password_valid:
            self.logger.warning(f"Invalid password for email: {login_data.email}")
            return create_problem_response(
                status_code=401,
                error_type="unauthorized",
                title="Unauthorized",
                detail="Invalid email or password",
                instance=str(request.url)
            )
        
        await self.user_repository.update_last_login(user.id)
        
        token_payload = {
            "user_id": str(user.id),
            "email": user.email,
            "name": user.name
        }
        
        access_token = token_tools.create_access_token(token_payload)
        refresh_token = token_tools.create_refresh_token(token_payload)
        
        self.logger.info(f"User logged in successfully: {login_data.email}")
        return {
            "accessToken": access_token,
            "refreshToken": refresh_token
        }

    @handle_validation_errors
    async def refresh_token(
        self,
        request: Request,
        data: pydantic_models.RefreshTokenRequest,
        token_tools: TokenTools
    ) -> Dict[str, str]:
        self.logger.info("Refresh token request received")
        
        new_access_token = token_tools.refresh_access_token(data.refresh_token)
        
        self.logger.info("Access token refreshed successfully")
        return {"accessToken": new_access_token}

    @handle_validation_errors
    async def logout(
        self,
        request: Request,
        token: str,
        token_tools: TokenTools
    ) -> None:
        if not token_tools.validate_token(token):
            return create_problem_response(
                status_code=401,
                error_type="unauthorized",
                title="Unauthorized",
                detail="Invalid token",
                instance=str(request.url)
            )
        
        self.logger.info("User logged out successfully")
        return None

    @handle_database_errors
    @handle_validation_errors
    async def get_current_user(
        self,
        request: Request,
        token: str,
        token_tools: TokenTools
    ) -> pydantic_models.UserResponse:
        if not token_tools.validate_token(token):
            return create_problem_response(
                status_code=401,
                error_type="unauthorized",
                title="Unauthorized",
                detail="Invalid or expired token",
                instance=str(request.url)
            )
        
        payload = token_tools.get_token_payload(token)
        user_id = payload.get("user_id")
        email = payload.get("email")
        name = payload.get("name")
        
        if not all([user_id, email, name]):
            return create_problem_response(
                status_code=401,
                error_type="unauthorized",
                title="Unauthorized",
                detail="Invalid token payload",
                instance=str(request.url)
            )
        
        user = await self.user_repository.get_by_id(user_id)
        
        if not user:
            return create_problem_response(
                status_code=404,
                error_type="not_found",
                title="Not Found",
                detail="User not found",
                instance=str(request.url)
            )
        
        if not user.is_active:
            return create_problem_response(
                status_code=403,
                error_type="forbidden",
                title="Forbidden",
                detail="User account is deactivated",
                instance=str(request.url)
            )
        
        user_data = pydantic_models.UserResponse(
            id=str(user.id),
            email=user.email,
            name=user.name
        )
        
        self.logger.info(f"User profile retrieved: {email}")
        return user_data