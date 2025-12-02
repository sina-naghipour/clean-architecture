import pytest
import pytest_asyncio
from unittest.mock import Mock, AsyncMock
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from main import app
from services.auth_services import AuthService
from authentication.tools import PasswordTools, TokenTools
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
        return repo

    @pytest_asyncio.fixture
    async def mock_request(self):
        request = Mock(spec=Request)
        request.url = "http://testserver/api/auth/register"
        return request

    @pytest_asyncio.fixture
    async def mock_password_tools(self):
        tools = Mock(spec=PasswordTools)
        tools.encode_password = Mock(return_value="hashed_password_123")
        tools.verify_password = Mock(return_value=True)
        return tools

    @pytest_asyncio.fixture
    async def mock_token_tools(self):
        tools = Mock(spec=TokenTools)
        tools.create_access_token = Mock(return_value="mock_access_token")
        tools.create_refresh_token = Mock(return_value="mock_refresh_token")
        tools.refresh_access_token = Mock(return_value="new_access_token")
        tools.validate_token = Mock(return_value=True)
        tools.get_token_payload = Mock(return_value={
            "user_id": "user_123",
            "email": "test@example.com",
            "name": "Test User"
        })
        return tools

    @pytest_asyncio.fixture
    async def auth_service(self, mock_logger, mock_user_repository):
        return AuthService(logger=mock_logger, user_repository=mock_user_repository)

    def test_client_initialization(self, client):
        response = client.get("/health")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_register_user_success(
        self, auth_service, mock_request, mock_password_tools, mock_user_repository
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
        mock_user_repository.email_exists.return_value = False
        mock_user_repository.create_user.return_value = mock_user

        result = await auth_service.register_user(
            mock_request, register_data, mock_password_tools
        )

        assert isinstance(result, JSONResponse)
        assert result.status_code == 201
        assert "Location" in result.headers
        assert "/api/users/user_123" in result.headers["Location"]
        
        mock_user_repository.email_exists.assert_called_once_with("test@example.com")
        mock_user_repository.create_user.assert_called_once()
        mock_password_tools.encode_password.assert_called_once_with("SecurePass123!")
        
        auth_service.logger.info.assert_any_call("Registration attempt for email: test@example.com")
        auth_service.logger.info.assert_any_call("User registered successfully: test@example.com")

    @pytest.mark.asyncio
    async def test_register_user_duplicate_email(
        self, auth_service, mock_request, mock_password_tools, mock_user_repository
    ):
        register_data = pydantic_models.User(
            email="existing@example.com",
            password="SecurePass123!",
            name="Test User"
        )

        mock_user_repository.email_exists.return_value = True

        result = await auth_service.register_user(
            mock_request, register_data, mock_password_tools
        )

        assert isinstance(result, JSONResponse)
        assert result.status_code == 409
        
        mock_user_repository.email_exists.assert_called_once_with("existing@example.com")
        mock_user_repository.create_user.assert_not_called()

    @pytest.mark.asyncio
    async def test_login_user_success(
        self, auth_service, mock_request, mock_password_tools, mock_token_tools, mock_user_repository
    ):
        login_data = pydantic_models.LoginRequest(
            email="test@example.com",
            password="CorrectPassword123!"
        )

        mock_user = Mock()
        mock_user.id = "user_123"
        mock_user.email = "test@example.com"
        mock_user.name = "Test User"
        mock_user.password = "hashed_password_123"
        mock_user_repository.get_active_user_by_email.return_value = mock_user
        mock_password_tools.verify_password.return_value = True

        result = await auth_service.login_user(
            mock_request, login_data, mock_password_tools, mock_token_tools
        )

        assert isinstance(result, dict)
        assert "accessToken" in result
        assert "refreshToken" in result
        assert result["accessToken"] == "mock_access_token"
        assert result["refreshToken"] == "mock_refresh_token"
        
        mock_user_repository.get_active_user_by_email.assert_called_once_with("test@example.com")
        mock_password_tools.verify_password.assert_called_once_with("CorrectPassword123!", "hashed_password_123")
        mock_user_repository.update_last_login.assert_called_once_with("user_123")
        
        auth_service.logger.info.assert_any_call("Login attempt for email: test@example.com")
        auth_service.logger.info.assert_any_call("User logged in successfully: test@example.com")

    @pytest.mark.asyncio
    async def test_login_user_invalid_email(
        self, auth_service, mock_request, mock_password_tools, mock_token_tools, mock_user_repository
    ):
        login_data = pydantic_models.LoginRequest(
            email="nonexistent@example.com",
            password="AnyPassword123!"
        )

        mock_user_repository.get_active_user_by_email.return_value = None

        result = await auth_service.login_user(
            mock_request, login_data, mock_password_tools, mock_token_tools
        )

        assert isinstance(result, JSONResponse)
        assert result.status_code == 401
        
        mock_user_repository.get_active_user_by_email.assert_called_once_with("nonexistent@example.com")
        mock_password_tools.verify_password.assert_not_called()
        
        auth_service.logger.warning.assert_called_once_with("Invalid login attempt for email: nonexistent@example.com")

    @pytest.mark.asyncio
    async def test_login_user_invalid_password(
        self, auth_service, mock_request, mock_password_tools, mock_token_tools, mock_user_repository
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
        mock_password_tools.verify_password.return_value = False

        result = await auth_service.login_user(
            mock_request, login_data, mock_password_tools, mock_token_tools
        )

        assert isinstance(result, JSONResponse)
        assert result.status_code == 401
        
        mock_user_repository.get_active_user_by_email.assert_called_once_with("test@example.com")
        mock_password_tools.verify_password.assert_called_once_with("WrongPassword", "hashed_password_123")
        
        auth_service.logger.warning.assert_called_once_with("Invalid password for email: test@example.com")

    @pytest.mark.asyncio
    async def test_refresh_token_success(
        self, auth_service, mock_request, mock_token_tools
    ):
        refresh_data = pydantic_models.RefreshTokenRequest(refreshToken="valid_refresh_token")

        result = await auth_service.refresh_token(
            mock_request, refresh_data, mock_token_tools
        )

        assert isinstance(result, dict)
        assert "accessToken" in result
        assert result["accessToken"] == "new_access_token"
        
        mock_token_tools.refresh_access_token.assert_called_once_with("valid_refresh_token")
        
        auth_service.logger.info.assert_any_call("Refresh token request received")
        auth_service.logger.info.assert_any_call("Access token refreshed successfully")

    @pytest.mark.asyncio
    async def test_logout_success(
        self, auth_service, mock_request, mock_token_tools
    ):
        valid_token = "valid_jwt_token"

        result = await auth_service.logout(
            mock_request, valid_token, mock_token_tools
        )

        assert result is None
        
        mock_token_tools.validate_token.assert_called_once_with(valid_token)
        
        auth_service.logger.info.assert_called_once_with("User logged out successfully")

    @pytest.mark.asyncio
    async def test_logout_invalid_token(
        self, auth_service, mock_request, mock_token_tools
    ):
        invalid_token = "invalid_jwt_token"
        mock_token_tools.validate_token.return_value = False

        result = await auth_service.logout(
            mock_request, invalid_token, mock_token_tools
        )

        assert isinstance(result, JSONResponse)
        assert result.status_code == 401
        
        mock_token_tools.validate_token.assert_called_once_with(invalid_token)

    @pytest.mark.asyncio
    async def test_get_current_user_success(
        self, auth_service, mock_request, mock_token_tools, mock_user_repository
    ):
        valid_token = "valid_jwt_token"

        mock_user = Mock()
        mock_user.id = "user_123"
        mock_user.email = "test@example.com"
        mock_user.name = "Test User"
        mock_user.is_active = True
        mock_user_repository.get_by_id.return_value = mock_user

        result = await auth_service.get_current_user(
            mock_request, valid_token, mock_token_tools
        )

        assert isinstance(result, pydantic_models.UserResponse)
        assert result.id == "user_123"
        assert result.email == "test@example.com"
        assert result.name == "Test User"
        
        mock_token_tools.validate_token.assert_called_once_with(valid_token)
        mock_token_tools.get_token_payload.assert_called_once_with(valid_token)
        mock_user_repository.get_by_id.assert_called_once_with("user_123")
        
        auth_service.logger.info.assert_called_once_with("User profile retrieved: test@example.com")

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(
        self, auth_service, mock_request, mock_token_tools
    ):
        invalid_token = "invalid_jwt_token"
        mock_token_tools.validate_token.return_value = False

        result = await auth_service.get_current_user(
            mock_request, invalid_token, mock_token_tools
        )

        assert isinstance(result, JSONResponse)
        assert result.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_not_found(
        self, auth_service, mock_request, mock_token_tools, mock_user_repository
    ):
        valid_token = "valid_jwt_token"
        mock_user_repository.get_by_id.return_value = None

        result = await auth_service.get_current_user(
            mock_request, valid_token, mock_token_tools
        )

        assert isinstance(result, JSONResponse)
        assert result.status_code == 404

    @pytest.mark.asyncio
    async def test_get_current_user_inactive(
        self, auth_service, mock_request, mock_token_tools, mock_user_repository
    ):
        valid_token = "valid_jwt_token"

        mock_user = Mock()
        mock_user.id = "user_123"
        mock_user.email = "test@example.com"
        mock_user.name = "Test User"
        mock_user.is_active = False
        mock_user_repository.get_by_id.return_value = mock_user

        result = await auth_service.get_current_user(
            mock_request, valid_token, mock_token_tools
        )

        assert isinstance(result, JSONResponse)
        assert result.status_code == 403

    @pytest.mark.asyncio
    async def test_service_initialization(self, mock_logger, mock_user_repository):
        service = AuthService(logger=mock_logger, user_repository=mock_user_repository)

        assert service.logger == mock_logger
        assert service.user_repository == mock_user_repository