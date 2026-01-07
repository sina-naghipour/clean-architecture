import pytest
import pytest_asyncio

from unittest.mock import Mock, AsyncMock

from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from main import app

from services.auth_service import AuthService
from services.token_service import TokenService
from services.password_service import PasswordService
from services.payments_grpc_client import PaymentGRPCClient
from services.token_cache import TokenCacheService

from database import pydantic_models
from repository.user_repository import UserRepository


class TestAuthService:
    @pytest.fixture
    def client(self):
        return TestClient(app)

    @pytest_asyncio.fixture
    async def mock_logger(self):
        return Mock()

    @pytest_asyncio.fixture
    async def mock_user_repository(self):
        repo = Mock(spec=UserRepository)
        repo.email_exists = AsyncMock()
        repo.create_user = AsyncMock()
        repo.get_active_user_by_email = AsyncMock()
        repo.update_last_login = AsyncMock()
        repo.get_by_id = AsyncMock()
        repo.get_user_by_referral_code = AsyncMock()
        repo.get_referrals_by_user = AsyncMock()
        repo.get_user_by_id = AsyncMock()
        repo.update = AsyncMock()
        return repo

    @pytest_asyncio.fixture
    async def mock_request(self):
        request = Mock(spec=Request)
        request.url = "http://testserver/api/auth/register"
        return request

    @pytest_asyncio.fixture
    async def mock_password_service(self):
        service = Mock(spec=PasswordService)
        service.encode_password = Mock(return_value="hashed_password_123")
        service.verify_password = Mock(return_value=True)
        return service

    @pytest_asyncio.fixture
    async def mock_token_service(self):
        service = Mock(spec=TokenService)
        service.create_access_token = Mock(return_value="mock_access_token")
        service.create_refresh_token = Mock(return_value="mock_refresh_token")
        service.refresh_access_token = Mock(return_value="new_access_token")
        service.validate_token = Mock(return_value=True)
        service.get_token_payload = Mock(return_value={
            "user_id": "user_123",
            "email": "test@example.com",
            "name": "Test User",
            "role": "user",
            "referrer_id": None
        })
        return service

    @pytest_asyncio.fixture
    async def mock_token_cache(self):
        cache = Mock(spec=TokenCacheService)
        cache.is_token_blacklisted = AsyncMock(return_value=False)
        cache.get_refresh_token = AsyncMock(return_value=None)
        cache.blacklist_token = AsyncMock(return_value=True)
        cache.get_cached_profile = AsyncMock(return_value=None)
        cache.cache_user_profile = AsyncMock(return_value=True)
        cache.store_refresh_token = AsyncMock(return_value=True)
        return cache

    @pytest_asyncio.fixture
    async def mock_payments_grpc_client(self):
        client = Mock(spec=PaymentGRPCClient)
        client.get_commission_report = AsyncMock(return_value={
            'referrer_id': 'user_123',
            'total_commissions': 5,
            'total_amount': 100.0,
            'pending_amount': 50.0,
            'paid_amount': 50.0,
            'commissions': []
        })
        return client

    @pytest_asyncio.fixture
    async def auth_service(self, mock_logger, mock_user_repository, mock_password_service, mock_token_service, mock_token_cache, mock_payments_grpc_client):
        service = AuthService(
            logger=mock_logger, 
            user_repository=mock_user_repository,
            password_service=mock_password_service,
            token_service=mock_token_service,
            payments_grpc_client=mock_payments_grpc_client
        )
        service.token_cache = mock_token_cache
        return service

    def test_client_initialization(self, client):
        response = client.get("/health")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_register_user_success(
        self, auth_service, mock_request, mock_user_repository
    ):
        register_data = pydantic_models.User(
            email="test@example.com",
            password="SecurePass123!",
            name="Test User"
        )

        mock_user = Mock()
        mock_user.id = "user_123"
        mock_user.email = "test@example.com"
        mock_user.name = "Test User"
        mock_user.referred_by = None
        mock_user.referral_code = None
        mock_user.referral_created_at = None
        mock_user_repository.email_exists.return_value = False
        mock_user_repository.create_user.return_value = mock_user

        result = await auth_service.register_user(
            mock_request, register_data
        )

        assert isinstance(result, JSONResponse)
        assert result.status_code == 201
        assert "Location" in result.headers
        assert "/api/users/user_123" in result.headers["Location"]
        
        mock_user_repository.email_exists.assert_called_once_with("test@example.com")
        mock_user_repository.create_user.assert_called_once()
        auth_service.password_service.encode_password.assert_called_once_with("SecurePass123!")
        
        auth_service.logger.info.assert_any_call("Registration attempt: test@example.com")
        auth_service.logger.info.assert_any_call("User registered: test@example.com")

    @pytest.mark.asyncio
    async def test_register_user_duplicate_email(
        self, auth_service, mock_request, mock_user_repository
    ):
        register_data = pydantic_models.User(
            email="existing@example.com",
            password="SecurePass123!",
            name="Test User"
        )

        mock_user_repository.email_exists.return_value = True

        result = await auth_service.register_user(
            mock_request, register_data
        )

        assert isinstance(result, JSONResponse)
        assert result.status_code == 409
        
        mock_user_repository.email_exists.assert_called_once_with("existing@example.com")
        mock_user_repository.create_user.assert_not_called()

    @pytest.mark.asyncio
    async def test_login_user_success(
        self, auth_service, mock_request, mock_user_repository, mock_token_cache
    ):
        login_data = pydantic_models.LoginRequest(
            email="test@example.com",
            password="CorrectPassword123!"
        )

        mock_user = Mock()
        mock_user.id = "user_123"
        mock_user.email = "test@example.com"
        mock_user.name = "Test User"
        mock_user.role = "user"
        mock_user.password = "hashed_password_123"
        mock_user_repository.get_active_user_by_email.return_value = mock_user
        auth_service.password_service.verify_password.return_value = True

        result = await auth_service.login_user(
            mock_request, login_data
        )

        assert isinstance(result, dict)
        assert "accessToken" in result
        assert "refreshToken" in result
        assert result["accessToken"] == "mock_access_token"
        assert result["refreshToken"] == "mock_refresh_token"
        
        mock_user_repository.get_active_user_by_email.assert_called_once_with("test@example.com")
        auth_service.password_service.verify_password.assert_called_once_with("CorrectPassword123!", "hashed_password_123")
        mock_user_repository.update_last_login.assert_called_once_with("user_123")
        mock_token_cache.store_refresh_token.assert_called_once_with("user_123", "mock_refresh_token")
        
        auth_service.logger.info.assert_any_call("Login attempt: test@example.com")
        auth_service.logger.info.assert_any_call("User logged in: test@example.com")

    @pytest.mark.asyncio
    async def test_login_user_invalid_email(
        self, auth_service, mock_request, mock_user_repository
    ):
        login_data = pydantic_models.LoginRequest(
            email="nonexistent@example.com",
            password="AnyPassword123!"
        )

        mock_user_repository.get_active_user_by_email.return_value = None

        result = await auth_service.login_user(
            mock_request, login_data
        )

        assert isinstance(result, JSONResponse)
        assert result.status_code == 401
        
        mock_user_repository.get_active_user_by_email.assert_called_once_with("nonexistent@example.com")
        auth_service.password_service.verify_password.assert_not_called()
        
        auth_service.logger.warning.assert_called_once_with("Invalid login: nonexistent@example.com")

    @pytest.mark.asyncio
    async def test_login_user_invalid_password(
        self, auth_service, mock_request, mock_user_repository
    ):
        login_data = pydantic_models.LoginRequest(
            email="test@example.com",
            password="WrongPassword"
        )

        mock_user = Mock()
        mock_user.id = "user_123"
        mock_user.email = "test@example.com"
        mock_user.name = "Test User"
        mock_user.password = "hashed_password_123"
        mock_user_repository.get_active_user_by_email.return_value = mock_user
        auth_service.password_service.verify_password.return_value = False

        result = await auth_service.login_user(
            mock_request, login_data
        )

        assert isinstance(result, JSONResponse)
        assert result.status_code == 401
        
        mock_user_repository.get_active_user_by_email.assert_called_once_with("test@example.com")
        auth_service.password_service.verify_password.assert_called_once_with("WrongPassword", "hashed_password_123")
        
        auth_service.logger.warning.assert_called_once_with("Invalid password: test@example.com")

    @pytest.mark.asyncio
    async def test_refresh_token_success(
        self, auth_service, mock_request, mock_token_cache
    ):
        refresh_data = pydantic_models.RefreshTokenRequest(refreshToken="valid_refresh_token")
        mock_token_cache.get_refresh_token.return_value = "valid_refresh_token"

        result = await auth_service.refresh_token(
            mock_request, refresh_data
        )

        assert isinstance(result, dict)
        assert "accessToken" in result
        assert result["accessToken"] == "new_access_token"
        
        mock_token_cache.is_token_blacklisted.assert_called_once_with("valid_refresh_token")
        auth_service.token_service.get_token_payload.assert_called_once_with("valid_refresh_token")
        mock_token_cache.get_refresh_token.assert_called_once_with("user_123")
        auth_service.token_service.refresh_access_token.assert_called_once_with("valid_refresh_token")
        
        auth_service.logger.info.assert_any_call("Refresh token request")
        auth_service.logger.info.assert_any_call("Access token refreshed")

    @pytest.mark.asyncio
    async def test_refresh_token_blacklisted(
        self, auth_service, mock_request, mock_token_cache
    ):
        refresh_data = pydantic_models.RefreshTokenRequest(refreshToken="blacklisted_token")
        mock_token_cache.is_token_blacklisted.return_value = True

        result = await auth_service.refresh_token(
            mock_request, refresh_data
        )

        assert isinstance(result, JSONResponse)
        assert result.status_code == 401
        mock_token_cache.is_token_blacklisted.assert_called_once_with("blacklisted_token")

    @pytest.mark.asyncio
    async def test_refresh_token_invalid(
        self, auth_service, mock_request, mock_token_cache
    ):
        refresh_data = pydantic_models.RefreshTokenRequest(refreshToken="invalid_token")
        auth_service.token_service.get_token_payload.side_effect = ValueError("Invalid token")
        
        result = await auth_service.refresh_token(
            mock_request, refresh_data
        )
        
        assert isinstance(result, JSONResponse)
        assert result.status_code == 401
        mock_token_cache.is_token_blacklisted.assert_called_once_with("invalid_token")
        auth_service.token_service.get_token_payload.assert_called_once_with("invalid_token")

    @pytest.mark.asyncio
    async def test_logout_success(
        self, auth_service, mock_request, mock_token_cache
    ):
        valid_token = "valid_jwt_token"

        result = await auth_service.logout(
            mock_request, valid_token
        )

        assert result is None
        
        auth_service.token_service.validate_token.assert_called_once_with(valid_token)
        auth_service.token_service.get_token_payload.assert_called_once_with(valid_token)
        mock_token_cache.blacklist_token.assert_called_once_with(valid_token)
        mock_token_cache.get_refresh_token.assert_called_once_with("user_123")
        
        auth_service.logger.info.assert_called_once_with("User logged out")

    @pytest.mark.asyncio
    async def test_logout_invalid_token(
        self, auth_service, mock_request
    ):
        invalid_token = "invalid_jwt_token"
        auth_service.token_service.validate_token.return_value = False

        result = await auth_service.logout(
            mock_request, invalid_token
        )

        assert isinstance(result, JSONResponse)
        assert result.status_code == 401
        
        auth_service.token_service.validate_token.assert_called_once_with(invalid_token)

    @pytest.mark.asyncio
    async def test_get_current_user_success(
        self, auth_service, mock_request, mock_user_repository, mock_token_cache
    ):
        valid_token = "valid_jwt_token"

        mock_user = Mock()
        mock_user.id = "user_123"
        mock_user.email = "test@example.com"
        mock_user.name = "Test User"
        mock_user.is_active = True
        mock_user.role = "user"
        mock_user.referral_code = None
        mock_user.referral_created_at = None
        mock_user.referred_by = None
        mock_user_repository.get_by_id.return_value = mock_user

        result = await auth_service.get_current_user(
            mock_request, valid_token
        )

        assert isinstance(result, pydantic_models.UserResponse)
        assert result.id == "user_123"
        assert result.email == "test@example.com"
        assert result.name == "Test User"
        
        mock_token_cache.is_token_blacklisted.assert_called_once_with(valid_token)
        auth_service.token_service.validate_token.assert_called_once_with(valid_token)
        auth_service.token_service.get_token_payload.assert_called_once_with(valid_token)
        mock_token_cache.get_cached_profile.assert_called_once_with("user_123")
        mock_user_repository.get_by_id.assert_called_once_with("user_123")

    @pytest.mark.asyncio
    async def test_get_current_user_cached(
        self, auth_service, mock_request, mock_user_repository, mock_token_cache
    ):
        valid_token = "valid_jwt_token"
        cached_profile = {
            "id": "user_123",
            "email": "test@example.com",
            "name": "Test User"
        }
        mock_token_cache.get_cached_profile.return_value = cached_profile

        result = await auth_service.get_current_user(
            mock_request, valid_token
        )

        assert isinstance(result, pydantic_models.UserResponse)
        assert result.id == "user_123"
        assert result.email == "test@example.com"
        assert result.name == "Test User"
        mock_user_repository.get_by_id.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_current_user_blacklisted_token(
        self, auth_service, mock_request, mock_token_cache
    ):
        blacklisted_token = "blacklisted_jwt_token"
        mock_token_cache.is_token_blacklisted.return_value = True

        result = await auth_service.get_current_user(
            mock_request, blacklisted_token
        )

        assert isinstance(result, JSONResponse)
        assert result.status_code == 401
        mock_token_cache.is_token_blacklisted.assert_called_once_with(blacklisted_token)

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(
        self, auth_service, mock_request, mock_token_cache
    ):
        invalid_token = "invalid_jwt_token"
        auth_service.token_service.validate_token.return_value = False

        result = await auth_service.get_current_user(
            mock_request, invalid_token
        )

        assert isinstance(result, JSONResponse)
        assert result.status_code == 401
        mock_token_cache.is_token_blacklisted.assert_called_once_with(invalid_token)

    @pytest.mark.asyncio
    async def test_get_current_user_not_found(
        self, auth_service, mock_request, mock_user_repository, mock_token_cache
    ):
        valid_token = "valid_jwt_token"
        mock_user_repository.get_by_id.return_value = None

        result = await auth_service.get_current_user(
            mock_request, valid_token
        )

        assert isinstance(result, JSONResponse)
        assert result.status_code == 404
        mock_token_cache.is_token_blacklisted.assert_called_once_with(valid_token)
        auth_service.token_service.validate_token.assert_called_once_with(valid_token)
        auth_service.token_service.get_token_payload.assert_called_once_with(valid_token)
        mock_user_repository.get_by_id.assert_called_once_with("user_123")

    @pytest.mark.asyncio
    async def test_get_current_user_inactive(
        self, auth_service, mock_request, mock_user_repository, mock_token_cache
    ):
        valid_token = "valid_jwt_token"

        mock_user = Mock()
        mock_user.id = "user_123"
        mock_user.email = "test@example.com"
        mock_user.name = "Test User"
        mock_user.is_active = False
        mock_user_repository.get_by_id.return_value = mock_user

        result = await auth_service.get_current_user(
            mock_request, valid_token
        )

        assert isinstance(result, JSONResponse)
        assert result.status_code == 403
        mock_token_cache.is_token_blacklisted.assert_called_once_with(valid_token)
        auth_service.token_service.validate_token.assert_called_once_with(valid_token)
        auth_service.token_service.get_token_payload.assert_called_once_with(valid_token)
        mock_user_repository.get_by_id.assert_called_once_with("user_123")

    @pytest.mark.asyncio
    async def test_service_initialization(
        self, mock_logger, mock_user_repository, mock_password_service, 
        mock_token_service, mock_payments_grpc_client
    ):
        service = AuthService(
            logger=mock_logger, 
            user_repository=mock_user_repository,
            password_service=mock_password_service,
            token_service=mock_token_service,
            payments_grpc_client=mock_payments_grpc_client
        )

        assert service.logger == mock_logger
        assert service.user_repository == mock_user_repository
        assert service.password_service == mock_password_service
        assert service.token_service == mock_token_service
        assert service.payments_grpc_client == mock_payments_grpc_client

    @pytest.mark.asyncio
    async def test_generate_referral_code(
        self, auth_service, mock_request, mock_user_repository
    ):
        import uuid
        import datetime
        
        user_id = "123e4567-e89b-12d3-a456-426614174000"
        user_uuid = uuid.UUID(user_id)
        
        mock_user = Mock()
        mock_user.id = user_uuid
        mock_user.referral_code = None
        mock_user_repository.get_user_by_id.return_value = mock_user
        
        result = await auth_service.generate_referral_code(
            mock_request, user_id
        )
        
        assert isinstance(result, dict)
        assert "referral_code" in result
        assert "message" in result
        assert result["message"] == "Referral code generated"
        
        mock_user_repository.get_user_by_id.assert_called_once_with(user_uuid)
        mock_user_repository.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_referrer_by_code(
        self, auth_service, mock_request, mock_user_repository
    ):
        referral_code = "REF_12345678_1234"
        
        mock_user = Mock()
        mock_user.id = "user_123"
        mock_user.email = "referrer@example.com"
        mock_user.name = "Referrer User"
        mock_user.referral_code = referral_code
        mock_user_repository.get_user_by_referral_code.return_value = mock_user
        
        result = await auth_service.get_referrer_by_code(
            mock_request, referral_code
        )
        
        assert isinstance(result, dict)
        assert result["referrer_id"] == "user_123"
        assert result["referrer_email"] == "referrer@example.com"
        assert result["referrer_name"] == "Referrer User"
        assert result["referral_code"] == referral_code
        
        mock_user_repository.get_user_by_referral_code.assert_called_once_with(referral_code)

    @pytest.mark.asyncio
    async def test_get_user_referrals(
        self, auth_service, mock_request, mock_user_repository
    ):
        user_id = "user_123"
        import datetime
        
        mock_referral1 = Mock()
        mock_referral1.id = "ref_456"
        mock_referral1.email = "referral1@example.com"
        mock_referral1.name = "Referral User 1"
        mock_referral1.created_at = datetime.datetime.now()
        
        mock_referral2 = Mock()
        mock_referral2.id = "ref_789"
        mock_referral2.email = "referral2@example.com"
        mock_referral2.name = "Referral User 2"
        mock_referral2.created_at = datetime.datetime.now()
        
        mock_user_repository.get_referrals_by_user.return_value = [mock_referral1, mock_referral2]
        
        result = await auth_service.get_user_referrals(
            mock_request, user_id
        )
        
        assert isinstance(result, dict)
        assert result["referrer_id"] == user_id
        assert result["total_referrals"] == 2
        assert len(result["referrals"]) == 2
        
        mock_user_repository.get_referrals_by_user.assert_called_once_with(user_id)

    @pytest.mark.asyncio
    async def test_get_commission_report_success(
        self, auth_service, mock_request, mock_payments_grpc_client
    ):
        referrer_id = "user_123"
        
        result = await auth_service.get_commission_report(
            mock_request, referrer_id
        )
        
        assert isinstance(result, dict)
        assert result["referrer_id"] == "user_123"
        assert result["total_commissions"] == 5
        assert result["total_amount"] == 100.0
        assert result["pending_amount"] == 50.0
        assert result["paid_amount"] == 50.0
        
        mock_payments_grpc_client.get_commission_report.assert_called_once_with(referrer_id)

    @pytest.mark.asyncio
    async def test_get_commission_report_service_unavailable(
        self, auth_service, mock_request, mock_payments_grpc_client
    ):
        referrer_id = "user_123"
        mock_payments_grpc_client.get_commission_report.return_value = {
            'referrer_id': referrer_id,
            'total_commissions': 0,
            'total_amount': 0.0,
            'pending_amount': 0.0,
            'paid_amount': 0.0,
            'commissions': [],
            'service_unavailable': True
        }
        
        result = await auth_service.get_commission_report(
            mock_request, referrer_id
        )
        
        assert isinstance(result, dict)
        assert result["service_unavailable"] is True
        
        mock_payments_grpc_client.get_commission_report.assert_called_once_with(referrer_id)

    @pytest.mark.asyncio
    async def test_register_user_with_referral_code(
        self, auth_service, mock_request, mock_user_repository
    ):
        import uuid
        
        referral_code = "REF_12345678_1234"
        referrer_id = uuid.uuid4()
        
        mock_referrer = Mock()
        mock_referrer.id = referrer_id
        mock_referrer.email = "referrer@example.com"
        mock_referrer.name = "Referrer User"
        mock_referrer.referral_code = referral_code
        
        mock_user_repository.get_user_by_referral_code.return_value = mock_referrer
        mock_user_repository.email_exists.return_value = False
        
        mock_user = Mock()
        mock_user.id = "user_123"
        mock_user.email = "newuser@example.com"
        mock_user.name = "New User"
        mock_user.referred_by = referrer_id
        mock_user.referral_code = None
        mock_user.referral_created_at = None
        mock_user_repository.create_user.return_value = mock_user
        
        register_data = pydantic_models.User(
            email="newuser@example.com",
            password="SecurePass123!",
            name="New User",
            referral_code=referral_code
        )
        
        result = await auth_service.register_user(
            mock_request, register_data
        )
        
        assert isinstance(result, JSONResponse)
        assert result.status_code == 201
        
        mock_user_repository.get_user_by_referral_code.assert_called_once_with(referral_code)
        mock_user_repository.email_exists.assert_called_once_with("newuser@example.com")
        mock_user_repository.create_user.assert_called_once()