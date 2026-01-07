import pytest
from httpx import AsyncClient
from main import app
import asyncio


class TestAuthAPIContract:
    @pytest.fixture
    def event_loop(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        yield loop
        loop.close()

    @pytest.fixture
    async def client(self):
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac

    @pytest.mark.asyncio
    async def test_health_endpoint(self, client):
        response = await client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "service" in data
        assert "timestamp" in data
        assert data["service"] == "authentication"

    @pytest.mark.asyncio
    async def test_root_endpoint(self, client):
        response = await client.get("/info")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "docs" in data
        assert "health" in data

    @pytest.mark.asyncio
    async def test_register_user_contract(self, client):
        register_data = {
            "email": "contract@test.com",
            "password": "SecurePass123!",
            "name": "Contract Test User"
        }
        
        response = await client.post("/register", json=register_data)
        
        assert response.status_code in [201, 409]
        
        if response.status_code == 201:
            data = response.json()
            assert "id" in data
            assert "email" in data
            assert "name" in data
            assert data["email"] == register_data["email"]
            assert data["name"] == register_data["name"]
            
            assert "Location" in response.headers
            assert "/api/users/" in response.headers["Location"]

    @pytest.mark.asyncio
    async def test_register_user_validation_contract(self, client):
        invalid_data = {
            "email": "invalid-email",
            "password": "weak",
            "name": ""
        }
        
        response = await client.post("/register", json=invalid_data)
        
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_login_user_contract(self, client):
        login_data = {
            "email": "test@example.com",
            "password": "CorrectPassword123!"
        }
        
        response = await client.post("/login", json=login_data)
        
        assert response.status_code in [200, 401]
        
        if response.status_code == 200:
            data = response.json()
            assert "accessToken" in data
            assert "refreshToken" in data
            assert isinstance(data["accessToken"], str)
            assert isinstance(data["refreshToken"], str)

    @pytest.mark.asyncio
    async def test_login_user_invalid_contract(self, client):
        login_data = {
            "email": "test@example.com",
            "password": "WrongPassword"
        }
        
        response = await client.post("/login", json=login_data)
        
        if response.status_code == 401:
            data = response.json()
            assert "type" in data
            assert "title" in data
            assert "status" in data
            assert "detail" in data
            assert data["status"] == 401
            assert data["title"] == "Unauthorized"

    @pytest.mark.asyncio
    async def test_refresh_token_contract(self, client):
        refresh_data = {
            "refreshToken": "mock_refresh_token"
        }
        
        response = await client.post("/refresh-token", json=refresh_data)
        
        assert response.status_code in [200, 400, 401]
        
        if response.status_code == 200:
            data = response.json()
            assert "accessToken" in data
            assert isinstance(data["accessToken"], str)

    @pytest.mark.asyncio
    async def test_get_current_user_contract(self, client):
        response = await client.get("/me")
        assert response.status_code == 401
        
        response = await client.get("/me", headers={"Authorization": "Invalid"})
        assert response.status_code == 401
        
        response = await client.get("/me", headers={"Authorization": "Bearer invalid_token"})
        assert response.status_code in [200, 401]

    @pytest.mark.asyncio
    async def test_logout_contract(self, client):
        response = await client.post("/logout")
        assert response.status_code == 401
        
        response = await client.post("/logout", headers={"Authorization": "Bearer mock_token"})
        assert response.status_code in [204, 401]

    @pytest.mark.asyncio
    async def test_problem_json_response_contract(self, client):
        login_data = {
            "email": "test@example.com",
            "password": "WrongPassword"
        }
        response = await client.post("/login", json=login_data)
        
        if response.status_code == 401:
            data = response.json()
            assert "type" in data
            assert "title" in data
            assert "status" in data
            assert "detail" in data
            assert data["status"] == 401

    @pytest.mark.asyncio
    async def test_generate_referral_code_contract(self, client):
        user_id = "123e4567-e89b-12d3-a456-426614174000"
        response = await client.post(f"/users/{user_id}/generate-referral")
        assert response.status_code in [401, 403, 404]

    @pytest.mark.asyncio
    async def test_get_referrer_by_code_contract(self, client):
        response = await client.get("/users/referrer/REF_12345678_1234")
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            assert "referrer_id" in data
            assert "referrer_email" in data
            assert "referrer_name" in data
            assert "referral_code" in data

    @pytest.mark.asyncio
    async def test_get_user_referrals_contract(self, client):
        user_id = "123e4567-e89b-12d3-a456-426614174000"
        response = await client.get(f"/users/{user_id}/referrals")
        assert response.status_code in [401, 403, 404]

    @pytest.mark.asyncio
    async def test_commission_report_contract(self, client):
        user_id = "123e4567-e89b-12d3-a456-426614174000"
        response = await client.get(f"/users/{user_id}/commission-report")
        assert response.status_code in [401, 403, 404]

    @pytest.mark.asyncio
    async def test_cleanup_test_data_contract(self, client):
        response = await client.delete("/cleanup-test-data")
        assert response.status_code in [204, 401]

    @pytest.mark.asyncio
    async def test_rate_limiting_contract(self, client):
        for i in range(6):
            login_data = {
                "email": f"test{i}@example.com",
                "password": "Password123!"
            }
            response = await client.post("/login", json=login_data)
            await asyncio.sleep(0.1)
        
        assert response.status_code in [401, 429]


class TestAuthAPIErrorScenarios:
    @pytest.fixture
    def event_loop(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        yield loop
        loop.close()

    @pytest.fixture
    async def client(self):
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac

    @pytest.mark.asyncio
    async def test_malformed_json_contract(self, client):
        response = await client.post(
            "/register",
            content="{invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_unsupported_media_type_contract(self, client):
        response = await client.post(
            "/register",
            content="email=test@test.com",
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_method_not_allowed_contract(self, client):
        response = await client.put("/register")
        assert response.status_code == 405

    @pytest.mark.asyncio
    async def test_cors_headers_contract(self, client):
        response = await client.get("/health", headers={"Origin": "http://localhost:3000"})
        
        if "access-control-allow-origin" in response.headers:
            assert response.headers["access-control-allow-origin"] == "http://localhost:3000"

    @pytest.mark.asyncio
    async def test_invalid_refresh_token_format(self, client):
        response = await client.post("/refresh-token", json={"refreshToken": ""})
        assert response.status_code in [400, 401]

    @pytest.mark.asyncio
    async def test_missing_refresh_token(self, client):
        response = await client.post("/refresh-token", json={})
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_invalid_auth_header_format(self, client):
        response = await client.get("/me", headers={"Authorization": "InvalidToken"})
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_empty_authorization_header(self, client):
        response = await client.get("/me", headers={"Authorization": ""})
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_password_change_endpoint_not_found(self, client):
        response = await client.post("/change-password", json={
            "oldPassword": "short",
            "newPassword": "weak"
        })
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_referral_code_invalid_format(self, client):
        response = await client.get("/users/referrer/invalid_code_format")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_user_id_invalid_uuid(self, client):
        response = await client.get("/users/invalid-uuid/referrals")
        assert response.status_code in [401, 422]

    @pytest.mark.asyncio
    async def test_nonexistent_endpoint(self, client):
        response = await client.get("/nonexistent")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_large_payload(self, client):
        large_payload = {
            "email": "test@example.com",
            "password": "A" * 1000,
            "name": "Test User"
        }
        response = await client.post("/register", json=large_payload)
        assert response.status_code == 422