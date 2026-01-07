from optl.trace_decorator import trace_service_operation
from .auth_helpers import create_problem_response
from decorators.auth_services_decorators import handle_database_errors, handle_validation_errors
from cache.redis_manager import redis_manager
from services.token_cache import TokenCacheService
from fastapi import Request
from fastapi.responses import JSONResponse
import hashlib
import json
import time
import uuid
from typing import Dict, Optional, Any
from datetime import datetime

from services.token_service import TokenService
from services.password_service import PasswordService
from database import pydantic_models
from repository.user_repository import UserRepository
from .payments_grpc_client import PaymentGRPCClient


class AuthService:
    def __init__(self, logger, user_repository: UserRepository, password_service: PasswordService, token_service: TokenService, payments_grpc_client: PaymentGRPCClient):
        self.logger = logger
        self.user_repository = user_repository
        self.password_service = password_service
        self.token_service = token_service
        self.token_cache = TokenCacheService(redis_manager)
        self.payments_grpc_client = payments_grpc_client
        
    @handle_database_errors
    @handle_validation_errors
    @trace_service_operation("register_user")
    async def register_user(self, request: Request, register_data: pydantic_models.User):
        self.logger.info(f"Registration attempt: {register_data.email}")
        
        user_exists = await self.user_repository.email_exists(register_data.email)
        
        if user_exists:
            return create_problem_response(
                status_code=409,
                error_type="conflict",
                title="Conflict",
                detail="User with this email already exists",
                instance=str(request.url)
            )
        
        referred_by_user = None
        if register_data.referral_code:
            referrer = await self.get_referrer_by_code(request, register_data.referral_code)
            if referrer:
                referred_by_user = uuid.UUID(referrer["referrer_id"])
        
        hashed_password = self.password_service.encode_password(register_data.password)
        
        user_dict = {
            "email": register_data.email,
            "password": hashed_password,
            "name": register_data.name,
            "referred_by": referred_by_user,
        }
        
        user = await self.user_repository.create_user(user_dict)
        
        user_response = pydantic_models.UserResponse(
            id=str(user.id),
            email=user.email,
            name=user.name,
            referred_by=str(user.referred_by) if user.referred_by else None,
            referral_code=user.referral_code,
            referral_created_at=user.referral_created_at.isoformat() if user.referral_created_at else None
        )
        
        self.logger.info(f"User registered: {register_data.email}")
        
        return JSONResponse(
            status_code=201,
            content=user_response.model_dump(),
            headers={"Location": f"/api/users/{user_response.id}"}
        )

    @handle_database_errors
    @trace_service_operation("login_user")
    async def login_user(self, request: Request, login_data: pydantic_models.LoginRequest):
        self.logger.info(f"Login attempt: {login_data.email}")
        
        password_hash = hashlib.md5(login_data.password.encode()).hexdigest()
        cache_key = f"login:{login_data.email}:{password_hash}"
        redis_client = await redis_manager.get_client()
        
        if redis_client:
            try:
                cached = await redis_client.get(cache_key)
                if cached:
                    cached_data = json.loads(cached)
                    token = cached_data.get("accessToken", "")
                    if token and not await self.token_cache.is_token_blacklisted(token):
                        self.logger.info(f"Login cache hit: {login_data.email}")
                        return cached_data
            except:
                pass
        
        user = await self.user_repository.get_active_user_by_email(login_data.email)
        
        if not user:
            self.logger.warning(f"Invalid login: {login_data.email}")
            return create_problem_response(
                status_code=401,
                error_type="unauthorized",
                title="Unauthorized",
                detail="Invalid email or password",
                instance=str(request.url)
            )
        
        is_password_valid = self.password_service.verify_password(login_data.password, user.password)
        
        if not is_password_valid:
            self.logger.warning(f"Invalid password: {login_data.email}")
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
            "name": user.name,
            "role": user.role,
            "referrer_id" : str(user.referred_by)
        }
        
        access_token = self.token_service.create_access_token(token_payload)
        refresh_token = self.token_service.create_refresh_token(token_payload)
        
        await self.token_cache.store_refresh_token(str(user.id), refresh_token)
        
        result = {
            "accessToken": access_token,
            "refreshToken": refresh_token
        }
        
        if redis_client:
            try:
                await redis_client.setex(cache_key, 300, json.dumps(result))
            except:
                pass
        
        self.logger.info(f"User logged in: {login_data.email}")
        return result

    @handle_validation_errors
    @trace_service_operation("refresh_token")
    async def refresh_token(self, request: Request, data: pydantic_models.RefreshTokenRequest):
        self.logger.info("Refresh token request")
        
        try:
            if await self.token_cache.is_token_blacklisted(data.refresh_token):
                raise ValueError("Token blacklisted")
                
            payload = self.token_service.get_token_payload(data.refresh_token)
            user_id = payload.get("user_id")
            
            if not user_id:
                raise ValueError("Invalid token payload")
            
            stored_refresh = await self.token_cache.get_refresh_token(user_id)
            
            if not stored_refresh or stored_refresh != data.refresh_token:
                return create_problem_response(
                    status_code=401,
                    error_type="unauthorized",
                    title="Unauthorized",
                    detail="Invalid refresh token",
                    instance=str(request.url)
                )
            
            new_access_token = self.token_service.refresh_access_token(data.refresh_token)
            
            self.logger.info("Access token refreshed")
            return {"accessToken": new_access_token}
            
        except Exception as e:
            return create_problem_response(
                status_code=401,
                error_type="unauthorized",
                title="Unauthorized",
                detail="Invalid refresh token",
                instance=str(request.url)
            )

    @handle_validation_errors
    @trace_service_operation("logout")
    async def logout(self, request: Request, token: str):
        if not self.token_service.validate_token(token):
            return create_problem_response(
                status_code=401,
                error_type="unauthorized",
                title="Unauthorized",
                detail="Invalid token",
                instance=str(request.url)
            )
        
        try:
            payload = self.token_service.get_token_payload(token)
            user_id = payload.get("user_id")
            email = payload.get("email")
            
            await self.token_cache.blacklist_token(token)
            
            if user_id:
                await self.token_cache.invalidate_user_cache(user_id)
                refresh_token = await self.token_cache.get_refresh_token(user_id)
                if refresh_token:
                    await self.token_cache.blacklist_token(refresh_token)
                    await self.token_cache.remove_refresh_token(user_id)
                
                redis_client = await redis_manager.get_client()
                if redis_client and email:
                    try:
                        pattern = f"login:{email}:*"
                        keys = await redis_client.keys(pattern)
                        if keys:
                            await redis_client.delete(*keys)
                    except:
                        pass
        except:
            await self.token_cache.blacklist_token(token)
        
        self.logger.info("User logged out")
        return None

    @handle_database_errors
    @handle_validation_errors
    @trace_service_operation("get_current_user")
    async def get_current_user(self, request: Request, token: str):
        if not token:
            self.logger.warning("No token provided")
            return create_problem_response(
                status_code=401,
                error_type="unauthorized",
                title="Unauthorized",
                detail="No token provided",
                instance=str(request.url)
            )
        
        if await self.token_cache.is_token_blacklisted(token):
            self.logger.warning(f"Token blacklisted for request")
            return create_problem_response(
                status_code=401,
                error_type="unauthorized",
                title="Unauthorized",
                detail="Token has been revoked",
                instance=str(request.url)
            )
        
        if not self.token_service.validate_token(token):
            self.logger.warning(f"Invalid token for request")
            return create_problem_response(
                status_code=401,
                error_type="unauthorized",
                title="Unauthorized",
                detail="Invalid or expired token",
                instance=str(request.url)
            )
        
        payload = self.token_service.get_token_payload(token)
        user_id = payload.get("user_id")
        
        if not user_id:
            self.logger.warning(f"No user_id in token payload")
            return create_problem_response(
                status_code=401,
                error_type="unauthorized",
                title="Unauthorized",
                detail="Invalid token payload",
                instance=str(request.url)
            )
        
        cached_profile = await self.token_cache.get_cached_profile(user_id)
        if cached_profile:
            self.logger.info(f"🟢 CACHE HIT for user {user_id}")
            return pydantic_models.UserResponse(
                id=cached_profile["id"],
                email=cached_profile["email"],
                name=cached_profile["name"]
            )
        
        self.logger.info(f"🔴 CACHE MISS for user {user_id}")
        
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            self.logger.warning(f"User not found: {user_id}")
            return create_problem_response(
                status_code=404,
                error_type="not_found",
                title="Not Found",
                detail="User not found",
                instance=str(request.url)
            )
        
        if not user.is_active:
            self.logger.warning(f"User inactive: {user_id}")
            return create_problem_response(
                status_code=403,
                error_type="forbidden",
                title="Forbidden",
                detail="User account is deactivated",
                instance=str(request.url)
            )
        
        user_data = {
            "id": str(user.id),
            "email": user.email,
            "name": user.name,
            "referral_code": user.referral_code,
            "referral_created_at": user.referral_created_at.isoformat() if user.referral_created_at else None,
            "referred_by": user.referred_by
            
        }
        
        await self.token_cache.cache_user_profile(user_id, user_data)
        self.logger.info(f"🟡 CACHE SET for user {user_id}")
        return pydantic_models.UserResponse(
            id=str(user.id),
            email=user.email,
            name=user.name,
            referred_by=str(user.referred_by) if user.referred_by else None,
            referral_code=user.referral_code,
            referral_created_at=user.referral_created_at.isoformat() if user.referral_created_at else None 
        )
        
    @handle_database_errors
    @trace_service_operation("generate_referral_code")
    async def generate_referral_code(self, request: Request, user_id: str) -> Dict[str, str]:
        import time
        user_uuid = uuid.UUID(user_id)
        user = await self.user_repository.get_user_by_id(user_uuid)
        
        if not user:
            return create_problem_response(
                status_code=404,
                error_type="not-found",
                title="User not found",
                detail="User not found",
                instance=str(request.url)
            )        
        if user.referral_code:
            return {"referral_code": user.referral_code, "message": "User already has referral code"}
        
        code = f"REF_{user.id.hex[:8].upper()}_{int(time.time()) % 10000:04d}"
        
        user.referral_code = code
        user.referral_created_at = datetime.now()
        await self.user_repository.update(
            id=user_uuid,
            obj_in={"referral_code": code, "referral_created_at": datetime.now()}
        )        
        return {"referral_code": code, "message": "Referral code generated"}

    @handle_database_errors
    @trace_service_operation("get_referrer_by_code")
    async def get_referrer_by_code(self,request: Request, referral_code: str) -> Optional[Dict[str, Any]]:
        user = await self.user_repository.get_user_by_referral_code(referral_code)
        if not user:
            return None
        
        return {
            "referrer_id": str(user.id),
            "referrer_email": user.email,
            "referrer_name": user.name,
            "referral_code": user.referral_code
        }

    @handle_database_errors
    @trace_service_operation("get_user_referrals")
    async def get_user_referrals(self,request: Request, user_id: str) -> Dict[str, Any]:
        referrals = await self.user_repository.get_referrals_by_user(user_id)
        
        return {
            "referrer_id": user_id,
            "total_referrals": len(referrals),
            "referrals": [
                {
                    "user_id": str(ref.id),
                    "email": ref.email,
                    "name": ref.name,
                    "created_at": ref.created_at.isoformat()
                }
                for ref in referrals
            ]
        }

    async def get_commission_report(self, request, referrer_id: str) -> Dict[str, Any]:
        if not self.payments_grpc_client:
            self.logger.error("Commission client not initialized")
            return {
                'referrer_id': referrer_id,
                'total_commissions': 0,
                'total_amount': 0.0,
                'pending_amount': 0.0,
                'paid_amount': 0.0,
                'commissions': [],
                'error': 'Commission service not configured'
            }
        
        try:
            self.logger.info(f"Getting commission report for referrer: {referrer_id}")
            report = await self.payments_grpc_client.get_commission_report(referrer_id)
            
            if report.get('service_unavailable'):
                self.logger.warning(f"Commission service unavailable, returning empty report for {referrer_id}")
            
            return report
            
        except Exception as e:
            self.logger.error(f"Failed to get commission report: {str(e)}")
            return {
                'referrer_id': referrer_id,
                'total_commissions': 0,
                'total_amount': 0.0,
                'pending_amount': 0.0,
                'paid_amount': 0.0,
                'commissions': [],
                'error': str(e)
            }