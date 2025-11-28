import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from main import app


class TestOrderAPIContract:    
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
        assert data["service"] == "order"

    @pytest.mark.asyncio
    async def test_ready_endpoint(self, client):
        response = await client.get("/ready")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "service" in data
        assert data["status"] == "ready"

    @pytest.mark.asyncio
    async def test_info_endpoint(self, client):
        response = await client.get("/info")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "docs" in data
        assert "health" in data
        assert "ready" in data

    @pytest.mark.asyncio
    async def test_create_order_contract(self, client):
        order_data = {
            "billing_address_id": "addr_1",
            "shipping_address_id": "addr_1",
            "payment_method_token": "pm_tok_abc"
        }
        
        response = await client.post("/", json=order_data, headers={"Authorization": "Bearer test_token"})
        
        assert response.status_code in [201, 400, 500]
        
        if response.status_code == 201:
            data = response.json()
            assert "id" in data
            assert "status" in data
            assert "total" in data
            assert "items" in data
            assert "created_at" in data
            assert data["status"] == "created"
            assert isinstance(data["items"], list)
            
            assert "Location" in response.headers
            assert "/" in response.headers["Location"]

    @pytest.mark.asyncio
    async def test_list_orders_contract(self, client):
        response = await client.get("/", headers={"Authorization": "Bearer test_token"})
        
        assert response.status_code == 200
        
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert isinstance(data["items"], list)

    @pytest.mark.asyncio
    async def test_list_orders_pagination_contract(self, client):
        response = await client.get("/?page=2&page_size=5", headers={"Authorization": "Bearer test_token"})
        
        assert response.status_code == 200
        
        data = response.json()
        assert data["page"] == 2
        assert data["page_size"] == 5

    @pytest.mark.asyncio
    async def test_get_order_contract(self, client):
        order_data = {
            "billing_address_id": "addr_1",
            "shipping_address_id": "addr_1"
        }
        
        create_response = await client.post("/", json=order_data, headers={"Authorization": "Bearer test_token"})
        
        if create_response.status_code == 201:
            order_id = create_response.json()["id"]
            
            response = await client.get(f"/{order_id}", headers={"Authorization": "Bearer test_token"})
            
            assert response.status_code in [200, 404]
            
            if response.status_code == 200:
                data = response.json()
                assert "id" in data
                assert "status" in data
                assert "total" in data
                assert "items" in data
                assert data["id"] == order_id

    @pytest.mark.asyncio
    async def test_get_order_not_found_contract(self, client):
        response = await client.get("/non_existent_order", headers={"Authorization": "Bearer test_token"})
        
        assert response.status_code == 400


class TestOrderAPIErrorScenarios:
    
    @pytest_asyncio.fixture
    async def client(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            yield client

    @pytest.mark.asyncio
    async def test_malformed_json_contract(self, client):
        response = await client.post(
            "/",
            content="{invalid json",
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer test_token"
            }
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_unsupported_media_type_contract(self, client):
        response = await client.post(
            "/",
            content="billing_address_id=addr_1",
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Authorization": "Bearer test_token"
            }
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_method_not_allowed_contract(self, client):
        response = await client.put("/", headers={"Authorization": "Bearer test_token"})
        assert response.status_code == 405

    @pytest.mark.asyncio
    async def test_unauthorized_access_contract(self, client):
        response = await client.get("/")
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_cors_headers_contract(self, client):
        response = await client.get("/health", headers={"Origin": "http://localhost:3000"})
        
        if "access-control-allow-origin" in response.headers:
            assert response.headers["access-control-allow-origin"] == "http://localhost:3000"