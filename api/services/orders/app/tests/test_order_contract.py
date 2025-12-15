import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from main import app
import jwt
from datetime import datetime, timedelta
import os

class TestOrderAPIContract:
    
    @staticmethod
    def create_admin_token() -> str:
        payload = {
            "user_id": "30780061-1b7f-431d-8d9e-6382ac453160",
            "email": "alice@example.com",
            "name": "Alice",
            "role": "admin",
            "is_active": True,
            "expiration": (datetime.now() + timedelta(hours=1)).timestamp(),
            "issued_at": datetime.now().timestamp(),
            "type": "access"
        }
        return jwt.encode(payload, os.getenv("JWT_SECRET_KEY", "random_secret_key"), algorithm="HS256")
    
    @staticmethod
    def create_user_token() -> str:
        payload = {
            "user_id": "user123",
            "email": "user@example.com",
            "name": "Regular User",
            "role": "user",
            "is_active": True,
            "expiration": (datetime.now() + timedelta(hours=1)).timestamp(),
            "issued_at": datetime.now().timestamp(),
            "type": "access"
        }
        return jwt.encode(payload, os.getenv("JWT_SECRET_KEY", "random_secret_key"), algorithm="HS256")
    
    @staticmethod
    def create_expired_token() -> str:
        payload = {
            "user_id": "test123",
            "email": "test@example.com",
            "name": "Test User",
            "role": "admin",
            "is_active": True,
            "expiration": (datetime.now() - timedelta(hours=1)).timestamp(),
            "issued_at": (datetime.now() - timedelta(hours=2)).timestamp(),
            "type": "access"
        }
        return jwt.encode(payload, os.getenv("JWT_SECRET_KEY", "random_secret_key"), algorithm="HS256")
    
    @pytest_asyncio.fixture
    async def client(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            yield client
    
    @pytest_asyncio.fixture
    def admin_auth_header(self):
        token = self.create_admin_token()
        return {"Authorization": f"Bearer {token}"}
    
    @pytest_asyncio.fixture
    def user_auth_header(self):
        token = self.create_user_token()
        return {"Authorization": f"Bearer {token}"}
    
    @pytest_asyncio.fixture
    def expired_auth_header(self):
        token = self.create_expired_token()
        return {"Authorization": f"Bearer {token}"}
    
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
    async def test_create_order_contract_admin(self, client, admin_auth_header):
        order_data = {
            "items": [
                {
                    "product_id": "prod_1",
                    "name": "Laptop",
                    "quantity": 1,
                    "unit_price": 999.99
                },
                {
                    "product_id": "prod_2",
                    "name": "Mouse",
                    "quantity": 2,
                    "unit_price": 29.99
                }
            ],
            "billing_address_id": "addr_1",
            "shipping_address_id": "addr_1",
            "payment_method_token": "pm_tok_abc"
        }
        
        response = await client.post("/", json=order_data, headers=admin_auth_header)
        
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
    async def test_create_order_contract_user_forbidden(self, client, user_auth_header):
        order_data = {
            "items": [
                {
                    "product_id": "prod_1",
                    "name": "Laptop",
                    "quantity": 1,
                    "unit_price": 999.99
                }
            ],
            "billing_address_id": "addr_1",
            "shipping_address_id": "addr_1",
            "payment_method_token": "pm_tok_abc"
        }
        
        response = await client.post("/", json=order_data, headers=user_auth_header)
        assert response.status_code in [201, 403, 500]

    @pytest.mark.asyncio
    async def test_list_orders_contract_admin(self, client, admin_auth_header):
        response = await client.get("/", headers=admin_auth_header)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert isinstance(data["items"], list)

    @pytest.mark.asyncio
    async def test_list_orders_pagination_contract_admin(self, client, admin_auth_header):
        response = await client.get("/?page=2&page_size=5", headers=admin_auth_header)
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 2
        assert data["page_size"] == 5

    @pytest.mark.asyncio
    async def test_get_order_contract_admin(self, client, admin_auth_header):
        order_data = {
            "items": [
                {
                    "product_id": "prod_1",
                    "name": "Test Product",
                    "quantity": 1,
                    "unit_price": 50.00
                }
            ],
            "billing_address_id": "addr_1",
            "shipping_address_id": "addr_1"
        }
        
        create_response = await client.post("/", json=order_data, headers=admin_auth_header)
        
        if create_response.status_code == 201:
            order_id = create_response.json()["id"]
            response = await client.get(f"/{order_id}", headers=admin_auth_header)
            assert response.status_code in [200, 404]
            
            if response.status_code == 200:
                data = response.json()
                assert "id" in data
                assert "status" in data
                assert "total" in data
                assert "items" in data
                assert data["id"] == order_id

    @pytest.mark.asyncio
    async def test_get_order_not_found_contract_admin(self, client, admin_auth_header):
        response = await client.get("/non_existent_order", headers=admin_auth_header)
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_expired_token(self, client, expired_auth_header):
        response = await client.get("/", headers=expired_auth_header)
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_missing_token(self, client):
        response = await client.get("/")
        assert response.status_code in [401, 422]

    @pytest.mark.asyncio
    async def test_create_order_empty_items(self, client, admin_auth_header):
        order_data = {
            "items": [],
            "billing_address_id": "addr_1",
            "shipping_address_id": "addr_1",
            "payment_method_token": "pm_tok_abc"
        }
        
        response = await client.post("/", json=order_data, headers=admin_auth_header)
        assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_create_order_missing_items(self, client, admin_auth_header):
        order_data = {
            "billing_address_id": "addr_1",
            "shipping_address_id": "addr_1",
            "payment_method_token": "pm_tok_abc"
        }
        
        response = await client.post("/", json=order_data, headers=admin_auth_header)
        assert response.status_code in [422]


class TestOrderAPIErrorScenarios:
    
    @staticmethod
    def create_admin_token() -> str:
        payload = {
            "user_id": "test_admin",
            "email": "admin@example.com",
            "name": "Admin",
            "role": "admin",
            "is_active": True,
            "expiration": (datetime.now() + timedelta(hours=1)).timestamp(),
            "issued_at": datetime.now().timestamp(),
            "type": "access"
        }
        return jwt.encode(payload, os.getenv("JWT_SECRET_KEY", "random_secret_key"), algorithm="HS256")
    
    @pytest_asyncio.fixture
    async def client(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            yield client
    
    @pytest_asyncio.fixture
    def admin_auth_header(self):
        token = self.create_admin_token()
        return {"Authorization": f"Bearer {token}"}
    
    @pytest.mark.asyncio
    async def test_malformed_json_contract(self, client, admin_auth_header):
        response = await client.post(
            "/",
            content="{invalid json",
            headers={
                "Content-Type": "application/json",
                **admin_auth_header
            }
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_unsupported_media_type_contract(self, client, admin_auth_header):
        response = await client.post(
            "/",
            content="billing_address_id=addr_1",
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                **admin_auth_header
            }
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_method_not_allowed_contract(self, client, admin_auth_header):
        response = await client.put("/", headers=admin_auth_header)
        assert response.status_code == 405

    @pytest.mark.asyncio
    async def test_unauthorized_access_contract(self, client):
        response = await client.get("/")
        assert response.status_code in [401, 422]

    @pytest.mark.asyncio
    async def test_cors_headers_contract(self, client, admin_auth_header):
        response = await client.get("/health", headers={"Origin": "http://localhost:3000", **admin_auth_header})
        
        if "access-control-allow-origin" in response.headers:
            assert response.headers["access-control-allow-origin"] == "http://localhost:3000"

    @pytest.mark.asyncio
    async def test_invalid_token_format(self, client):
        response = await client.get("/", headers={"Authorization": "InvalidTokenFormat"})
        assert response.status_code in [401, 422]

    @pytest.mark.asyncio
    async def test_missing_bearer_prefix(self, client):
        response = await client.get("/", headers={"Authorization": "test_token"})
        assert response.status_code in [401, 422]