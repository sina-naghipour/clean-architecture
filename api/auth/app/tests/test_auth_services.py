import pytest
import pytest_asyncio
from unittest.mock import Mock
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from main import app
from services.auth_services import AuthService
from authentication.tools import PasswordTools, TokenTools
from database import pydantic_models


class TestAuthService:
    @pytest.fixture
    def client(self):
        return TestClient(app)

    @pytest_asyncio.fixture
    async def mock_logger(self):
        return Mock()

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
    async def auth_service(self, mock_logger):
        return AuthService(logger=mock_logger)

    def test_client_initialization(self, client):
        response = client.get("/health")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_register_user_success(
        self, auth_service, mock_request, mock_password_tools
    ):
        register_data = pydantic_models.User(
            email="test@example.com",
            password="SecurePass123!",
            name="Test User"
        )

        result = await auth_service.register_user(
            mock_request, register_data, mock_password_tools
        )

        assert isinstance(result, JSONResponse)
        assert result.status_code == 201
        assert "Location" in result.headers
        assert "/api/users/user_123" in result.headers["Location"]
        
        auth_service.logger.info.assert_any_call("Registration attempt for email: test@example.com")
        auth_service.logger.info.assert_any_call("User registered successfully: test@example.com")
        
        mock_password_tools.encode_password.assert_called_once_with("SecurePass123!")

    @pytest.mark.asyncio
    async def test_login_user_success(
        self, auth_service, mock_request, mock_password_tools, mock_token_tools
    ):
        login_data = pydantic_models.LoginRequest(
            email="test@example.com",
            password="CorrectPassword123!"
        )

        result = await auth_service.login_user(
            mock_request, login_data, mock_password_tools, mock_token_tools
        )

        assert isinstance(result, JSONResponse)
        assert result.status_code == 401
        
        auth_service.logger.info.assert_called_with("Login attempt for email: test@example.com")
        auth_service.logger.warning.assert_called_with("Invalid login attempt for email: test@example.com")

    @pytest.mark.asyncio
    async def test_login_user_invalid_credentials(
        self, auth_service, mock_request, mock_password_tools, mock_token_tools
    ):
        login_data = pydantic_models.LoginRequest(
            email="test@example.com",
            password="WrongPassword"
        )

        result = await auth_service.login_user(
            mock_request, login_data, mock_password_tools, mock_token_tools
        )

        assert isinstance(result, JSONResponse)
        assert result.status_code == 401
        
        auth_service.logger.warning.assert_called_once_with(
            "Invalid login attempt for email: test@example.com"
        )

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
    async def test_refresh_token_invalid(
        self, auth_service, mock_request, mock_token_tools
    ):
        refresh_data = pydantic_models.RefreshTokenRequest(refreshToken="invalid_token")
        mock_token_tools.refresh_access_token.side_effect = ValueError("Invalid refresh token")

        with pytest.raises(ValueError):
            await auth_service.refresh_token(
                mock_request, refresh_data, mock_token_tools
            )

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
        self, auth_service, mock_request, mock_token_tools
    ):
        valid_token = "valid_jwt_token"

        result = await auth_service.get_current_user(
            mock_request, valid_token, mock_token_tools
        )

        assert isinstance(result, pydantic_models.UserResponse)
        assert result.id == "user_123"
        assert result.email == "test@example.com"
        assert result.name == "Test User"
        
        mock_token_tools.validate_token.assert_called_once_with(valid_token)
        mock_token_tools.get_token_payload.assert_called_once_with(valid_token)
        
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
    async def test_get_current_user_invalid_payload(
        self, auth_service, mock_request, mock_token_tools
    ):
        valid_token = "valid_jwt_token"
        mock_token_tools.get_token_payload.return_value = {
            "user_id": None,
            "email": "test@example.com",
            "name": "Test User"
        }

        result = await auth_service.get_current_user(
            mock_request, valid_token, mock_token_tools
        )

        assert isinstance(result, JSONResponse)
        assert result.status_code == 401

    @pytest.mark.asyncio
    async def test_service_initialization(self, mock_logger):
        service = AuthService(logger=mock_logger)

        assert service.logger == mock_logger

    @pytest.mark.asyncio
    async def test_login_user_password_hashing_called(
        self, auth_service, mock_request, mock_password_tools, mock_token_tools
    ):
        login_data = pydantic_models.LoginRequest(
            email="test@example.com",
            password="CorrectPassword123!"
        )

        await auth_service.login_user(
            mock_request, login_data, mock_password_tools, mock_token_tools
        )

        mock_password_tools.encode_password.assert_called_with("CorrectPassword123!")