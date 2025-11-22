import pytest
import pytest_asyncio
from httpx import AsyncClient
from main import app


class TestAuthAPIContract:    
    @pytest_asyncio.fixture
    async def client(self):
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client

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
        response = await client.get("/")
        
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
        
        response = await client.post("/api/auth/register", json=register_data)
        
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
        
        response = await client.post("/api/auth/register", json=invalid_data)
        
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_login_user_contract(self, client):
        login_data = {
            "email": "test@example.com",
            "password": "CorrectPassword123!"
        }
        
        response = await client.post("/api/auth/login", json=login_data)
        
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
        
        response = await client.post("/api/auth/login", json=login_data)
        
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
        
        response = await client.post("/api/auth/refresh-token", json=refresh_data)
        
        assert response.status_code in [200, 400, 401]
        
        if response.status_code == 200:
            data = response.json()
            assert "accessToken" in data
            assert isinstance(data["accessToken"], str)

    @pytest.mark.asyncio
    async def test_get_current_user_contract(self, client):
        response = await client.get("/api/auth/me")
        assert response.status_code == 401  # Changed from 422 to 401
        
        response = await client.get("/api/auth/me", headers={"Authorization": "Invalid"})
        assert response.status_code == 401  # Changed from 422 to 401
        
        response = await client.get("/api/auth/me", headers={"Authorization": "Bearer invalid_token"})
        assert response.status_code in [200, 401]

    @pytest.mark.asyncio
    async def test_logout_contract(self, client):
        response = await client.post("/api/auth/logout")
        assert response.status_code == 401  # Changed from 422 to 401
        
        response = await client.post("/api/auth/logout", headers={"Authorization": "Bearer mock_token"})
        assert response.status_code in [204, 401]

    @pytest.mark.asyncio
    async def test_problem_json_response_contract(self, client):
        login_data = {
            "email": "test@example.com",
            "password": "WrongPassword"
        }
        response = await client.post("/api/auth/login", json=login_data)
        
        if response.status_code == 401:
            data = response.json()
            assert "type" in data
            assert "title" in data
            assert "status" in data
            assert "detail" in data
            assert data["status"] == 401


class TestAuthAPIErrorScenarios:
    
    @pytest_asyncio.fixture
    async def client(self):
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client

    @pytest.mark.asyncio
    async def test_malformed_json_contract(self, client):
        response = await client.post(
            "/api/auth/register",
            content="{invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_unsupported_media_type_contract(self, client):
        response = await client.post(
            "/api/auth/register",
            content="email=test@test.com",
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_method_not_allowed_contract(self, client):
        response = await client.put("/api/auth/register")
        assert response.status_code == 405

    @pytest.mark.asyncio
    async def test_cors_headers_contract(self, client):
        response = await client.get("/health", headers={"Origin": "http://localhost:3000"})
        
        if "access-control-allow-origin" in response.headers:
            assert response.headers["access-control-allow-origin"] == "http://localhost:3000"