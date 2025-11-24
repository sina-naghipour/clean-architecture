import pytest
import pytest_asyncio
from unittest.mock import Mock
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from main import app
from services.profile_services import ProfileService
from database import models


class TestProfileService:
    @pytest.fixture
    def client(self):
        return TestClient(app)

    @pytest_asyncio.fixture
    async def mock_logger(self):
        return Mock()

    @pytest_asyncio.fixture
    async def mock_request(self):
        request = Mock(spec=Request)
        request.url = "http://testserver/api/profile"
        return request

    @pytest_asyncio.fixture
    async def profile_service(self, mock_logger):
        service = ProfileService(logger=mock_logger)
        return service

    def test_client_initialization(self, client):
        response = client.get("/health")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_profile_success(
        self, profile_service, mock_request
    ):
        user_id = "user_123"

        result = await profile_service.get_profile(
            mock_request, user_id
        )

        assert isinstance(result, models.UserResponse)
        assert result.id == user_id
        assert result.email == "alice@example.com"
        assert result.name == "Alice"
        
        profile_service.logger.info.assert_any_call(f"Profile retrieval attempt for user: {user_id}")
        profile_service.logger.info.assert_any_call(f"Profile retrieved successfully for user: {user_id}")

    @pytest.mark.asyncio
    async def test_get_profile_not_found(
        self, profile_service, mock_request
    ):
        user_id = "non_existent_user"

        result = await profile_service.get_profile(
            mock_request, user_id
        )

        assert isinstance(result, JSONResponse)
        assert result.status_code == 404

    @pytest.mark.asyncio
    async def test_update_profile_success(
        self, profile_service, mock_request
    ):
        user_id = "user_123"
        profile_data = models.ProfileUpdate(
            name="Alice Updated",
            phone="+1987654321"
        )

        result = await profile_service.update_profile(
            mock_request, profile_data, user_id
        )

        assert isinstance(result, models.UserResponse)
        assert result.name == "Alice Updated"
        
        profile_service.logger.info.assert_any_call(f"Profile update attempt for user: {user_id}")
        profile_service.logger.info.assert_any_call(f"Profile updated successfully for user: {user_id}")

    @pytest.mark.asyncio
    async def test_update_profile_not_found(
        self, profile_service, mock_request
    ):
        user_id = "non_existent_user"
        profile_data = models.ProfileUpdate(name="New Name")

        result = await profile_service.update_profile(
            mock_request, profile_data, user_id
        )

        assert isinstance(result, JSONResponse)
        assert result.status_code == 404

    @pytest.mark.asyncio
    async def test_change_password_success(
        self, profile_service, mock_request
    ):
        user_id = "user_123"
        password_data = models.PasswordChange(
            old_password="current_password",
            new_password="new_secure_password"
        )

        result = await profile_service.change_password(
            mock_request, password_data, user_id
        )

        assert result == {"message": "Password updated successfully"}
        
        profile_service.logger.info.assert_any_call(f"Password change attempt for user: {user_id}")
        profile_service.logger.info.assert_any_call(f"Password changed successfully for user: {user_id}")

    @pytest.mark.asyncio
    async def test_change_password_incorrect_current(
        self, profile_service, mock_request
    ):
        user_id = "user_123"
        password_data = models.PasswordChange(
            old_password="wrong_password",
            new_password="new_secure_password"
        )

        result = await profile_service.change_password(
            mock_request, password_data, user_id
        )

        assert isinstance(result, JSONResponse)
        assert result.status_code == 400

    @pytest.mark.asyncio
    async def test_list_addresses_success(
        self, profile_service, mock_request
    ):
        user_id = "user_123"

        result = await profile_service.list_addresses(
            mock_request, user_id
        )

        assert isinstance(result, list)
        assert len(result) >= 1
        assert isinstance(result[0], models.AddressResponse)
        
        profile_service.logger.info.assert_any_call(f"Addresses listing attempt for user: {user_id}")
        profile_service.logger.info.assert_any_call(f"Addresses listed successfully for user: {user_id}")

    @pytest.mark.asyncio
    async def test_list_addresses_empty(
        self, profile_service, mock_request
    ):
        user_id = "user_with_no_addresses"

        result = await profile_service.list_addresses(
            mock_request, user_id
        )

        assert isinstance(result, list)
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_create_address_success(
        self, profile_service, mock_request
    ):
        user_id = "user_123"
        address_data = models.AddressRequest(
            line="789 Pine Road",
            city="Chicago",
            postal_code="60601",
            country="USA"
        )

        result = await profile_service.create_address(
            mock_request, address_data, user_id
        )

        assert isinstance(result, JSONResponse)
        assert result.status_code == 201
        
        profile_service.logger.info.assert_any_call(f"Address creation attempt for user: {user_id}")
        profile_service.logger.info.assert_any_call("Address created successfully: addr_1")

    @pytest.mark.asyncio
    async def test_update_address_success(
        self, profile_service, mock_request
    ):
        user_id = "user_123"
        address_id = "addr_1"
        address_data = models.AddressRequest(
            line="123 Main St Updated",
            city="New York",
            postal_code="10001",
            country="USA"
        )

        result = await profile_service.update_address(
            mock_request, address_id, address_data, user_id
        )

        assert isinstance(result, models.AddressResponse)
        assert result.line == "123 Main St Updated"
        
        profile_service.logger.info.assert_any_call(f"Address update attempt: {address_id}")
        profile_service.logger.info.assert_any_call(f"Address updated successfully: {address_id}")

    @pytest.mark.asyncio
    async def test_update_address_not_found(
        self, profile_service, mock_request
    ):
        user_id = "user_123"
        address_id = "non_existent_addr"
        address_data = models.AddressRequest(
            line="Test",
            city="Test",
            postal_code="12345",
            country="Test"
        )

        result = await profile_service.update_address(
            mock_request, address_id, address_data, user_id
        )

        assert isinstance(result, JSONResponse)
        assert result.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_address_success(
        self, profile_service, mock_request
    ):
        user_id = "user_123"
        address_id = "addr_1"

        result = await profile_service.delete_address(
            mock_request, address_id, user_id
        )

        assert isinstance(result, JSONResponse)
        assert result.status_code == 204
        
        profile_service.logger.info.assert_any_call(f"Address deletion attempt: {address_id}")
        profile_service.logger.info.assert_any_call(f"Address deleted successfully: {address_id}")

    @pytest.mark.asyncio
    async def test_delete_address_not_found(
        self, profile_service, mock_request
    ):
        user_id = "user_123"
        address_id = "non_existent_addr"

        result = await profile_service.delete_address(
            mock_request, address_id, user_id
        )

        assert isinstance(result, JSONResponse)
        assert result.status_code == 404

    @pytest.mark.asyncio
    async def test_service_initialization(self, mock_logger):
        service = ProfileService(logger=mock_logger)

        assert service.logger == mock_logger
        assert service.profiles != {}
        assert service.addresses != {}
        assert service.next_address_id == 1
