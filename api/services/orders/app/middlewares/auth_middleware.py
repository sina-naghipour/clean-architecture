from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable, List
from datetime import datetime
from dotenv import load_dotenv
from jwt import decode, ExpiredSignatureError, InvalidTokenError
import os
from services.order_helpers import create_problem_response

load_dotenv()
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "random_secret_key")

class UserRole:
    ADMIN = "admin"
    USER = "user"

class AuthMiddleware(BaseHTTPMiddleware):
    
    ALLOWED_ROLES: List[str] = [UserRole.ADMIN]
    
    @staticmethod
    def validate_token(token: str) -> dict:
        try:
            payload = decode(token, JWT_SECRET_KEY, algorithms=['HS256'])
            expiration = payload.get('expiration')
            if expiration and datetime.now().timestamp() > expiration:
                return {"valid": False, "error": "Token expired"}
            
            required_fields = ['user_id', 'email', 'role']
            for field in required_fields:
                if field not in payload:
                    return {"valid": False, "error": f"Missing field: {field}"}
            
            if payload.get('type') != 'access':
                return {"valid": False, "error": "Invalid token type"}
            
            return {
                "valid": True,
                "user_data": {
                    "id": payload['user_id'],
                    "email": payload['email'],
                    "name": payload.get('name'),
                    "role": payload['role'],
                    "is_active": payload.get('is_active', True)
                }
            }
            
        except ExpiredSignatureError:
            return {"valid": False, "error": "Token expired"}
        except InvalidTokenError:
            return {"valid": False, "error": "Invalid token"}
        except Exception as e:
            return {"valid": False, "error": str(e)}

    async def dispatch(self, request: Request, call_next: Callable):
        public_paths = ["/health", "/docs", "/openapi.json", "/redoc", "/ready", "/info"]
        if request.url.path in public_paths:
            return await call_next(request)
        
        auth_header = request.headers.get("Authorization", "")
        token = auth_header.replace("Bearer ", "") if auth_header.startswith("Bearer ") else None
        if token is None:
            return create_problem_response(
                status_code=401,
                error_type="unauthorized",
                title="Unauthorized",
                detail="Authorization header missing",
                instance=request.url.path
            )
        
        validation_result = self.validate_token(token)
        if not validation_result["valid"]:
            return create_problem_response(
                status_code=401,
                error_type="invalid_token",
                title="Invalid Token",
                detail=validation_result["error"],
                instance=request.url.path
            )
        
        user_role = validation_result["user_data"]["role"]
        if user_role not in self.ALLOWED_ROLES:
            return create_problem_response(
                status_code=403,
                error_type="forbidden",
                title="Forbidden",
                detail=f"Access denied. Required roles: {self.ALLOWED_ROLES}",
                instance=request.url.path
            )
        
        request.state.user = validation_result["user_data"]
        
        response = await call_next(request)
        
        return response