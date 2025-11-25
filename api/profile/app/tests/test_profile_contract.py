import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from main import app


class TestProfileAPIContract:    
    @pytest_asyncio.fixture
    async def client(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            yield client

    @pytest.mark.asyncio
    async def test_health_endpoint(self, client):
        response = await client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "service" in data
        assert "timestamp" in data
        assert data["service"] == "profile"

    @pytest.mark.asyncio
    async def test_ready_endpoint(self, client):
        response = await client.get("/ready")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "service" in data
        assert data["status"] == "ready"

    @pytest.mark.asyncio
    async def test_root_endpoint(self, client):
        response = await client.get("/info")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "docs" in data
        assert "health" in data
        assert "ready" in data

    @pytest.mark.asyncio
    async def test_get_profile_contract(self, client):
        response = await client.get("/", headers={"Authorization": "Bearer test_token"})
        
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "email" in data
        assert "name" in data

    @pytest.mark.asyncio
    async def test_update_profile_contract(self, client):
        profile_data = {
            "name": "Alice Updated",
            "phone": "+1234567890"
        }
        
        response = await client.patch("/", json=profile_data, headers={"Authorization": "Bearer test_token"})
        
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "email" in data
        assert "name" in data

    @pytest.mark.asyncio
    async def test_change_password_contract(self, client):
        password_data = {
            "old_password": "current_password",
            "new_password": "new_secure_password"
        }
        
        response = await client.patch("/password", json=password_data, headers={"Authorization": "Bearer test_token"})
        
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_list_addresses_contract(self, client):
        response = await client.get("/addresses", headers={"Authorization": "Bearer test_token"})
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_create_address_contract(self, client):
        address_data = {
            "line": "456 Oak Avenue",
            "city": "Los Angeles",
            "postal_code": "90001",
            "country": "USA"
        }
        
        response = await client.post("/addresses", json=address_data, headers={"Authorization": "Bearer test_token"})
        
        assert response.status_code in [201, 400]
        
        if response.status_code == 201:
            data = response.json()
            assert "id" in data
            assert "line" in data
            assert "city" in data
            assert "postal_code" in data
            assert "country" in data

    @pytest.mark.asyncio
    async def test_update_address_contract(self, client):
        address_data = {
            "line": "456 Oak Avenue Updated",
            "city": "Los Angeles",
            "postal_code": "90001",
            "country": "USA"
        }
        
        response = await client.patch("/addresses/addr_1", json=address_data, headers={"Authorization": "Bearer test_token"})
        
        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_delete_address_contract(self, client):
        response = await client.delete("/addresses/addr_1", headers={"Authorization": "Bearer test_token"})
        
        assert response.status_code in [204, 404]


class TestProfileAPIErrorScenarios:
    
    @pytest_asyncio.fixture
    async def client(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            yield client

    @pytest.mark.asyncio
    async def test_malformed_json_contract(self, client):
        response = await client.patch(
            "/",
            content="{invalid json",
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer test_token"
            }
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_unauthorized_access_contract(self, client):
        response = await client.get("/")
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_cors_headers_contract(self, client):
        response = await client.get("/health", headers={"Origin": "http://localhost:3000"})
        
        if "access-control-allow-origin" in response.headers:
            assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
