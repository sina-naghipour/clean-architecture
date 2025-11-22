from .auth_helpers import create_problem_response
from fastapi import Request
from fastapi.responses import JSONResponse
from typing import Dict
from authentication.tools import PasswordTools, TokenTools
from database import models

class AuthService:
    def __init__(self, logger):
        self.logger = logger

    async def register_user(
        self,
        request: Request,
        register_data: models.RegisterRequest,
        password_tools: PasswordTools
    ) -> models.UserResponse:
        self.logger.info(f"Registration attempt for email: {register_data.email}")
        
        user_exists = False
        
        if user_exists:
            return create_problem_response(
                status_code=409,
                error_type="conflict",
                title="Conflict",
                detail="Duplicate resource.",
                instance=str(request.url)
            )
        
        hashed_password = password_tools.encode_password(register_data.password)
        
        mock_user = models.UserResponse(
            id="user_123",
            email=register_data.email,
            name=register_data.name
        )
        
        self.logger.info(f"User registered successfully: {register_data.email}")
        
        response = JSONResponse(
            status_code=201,
            content=mock_user.dict(),
            headers={"Location": f"/api/users/{mock_user.id}"}
        )
        return response

    async def login_user(
        self,
        request: Request,
        login_data: models.LoginRequest,
        password_tools: PasswordTools,
        token_tools: TokenTools
    ) -> Dict[str, str]:
        self.logger.info(f"Login attempt for email: {login_data.email}")
        
        mock_user_data = {
            "id": "user_123",
            "email": login_data.email,
            "name": "Test User",
            "password_hash": password_tools.encode_password("CorrectPassword123!")
        }
        
        is_password_valid = False
        
        if not is_password_valid:
            self.logger.warning(f"Invalid login attempt for email: {login_data.email}")
            return create_problem_response(
                status_code=401,
                error_type="unauthorized",
                title="Unauthorized",
                detail="Invalid email or password",
                instance=str(request.url)
            )
        
        token_payload = {
            "user_id": mock_user_data["id"],
            "email": mock_user_data["email"],
            "name": mock_user_data["name"]
        }
        
        access_token = token_tools.create_access_token(token_payload)
        refresh_token = token_tools.create_refresh_token(token_payload)
        
        self.logger.info(f"User logged in successfully: {login_data.email}")
        return {
            "accessToken": access_token,
            "refreshToken": refresh_token
        }

    async def refresh_token(
        self,
        request: Request,
        refresh_data: models.RefreshTokenRequest,
        token_tools: TokenTools
    ) -> Dict[str, str]:
        self.logger.info("Refresh token request received")
        
        new_access_token = token_tools.refresh_access_token(refresh_data.refresh_token)
        
        self.logger.info("Access token refreshed successfully")
        return {"accessToken": new_access_token}

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

    async def get_current_user(
        self,
        request: Request,
        token: str,
        token_tools: TokenTools
    ) -> models.UserResponse:
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
        
        user_data = models.UserResponse(
            id=user_id,
            email=email,
            name=name
        )
        
        self.logger.info(f"User profile retrieved: {email}")
        return user_data