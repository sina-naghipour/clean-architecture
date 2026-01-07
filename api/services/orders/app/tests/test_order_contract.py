import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from main import app
import jwt
from datetime import datetime, timedelta
import os
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from uuid import uuid4
import json

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
            "type": "access",
            "referrer_id": None
        }
        return jwt.encode(payload, os.getenv("JWT_SECRET_KEY", "random_secret_key"), algorithm="HS256")
    
    @staticmethod
    def create_user_token() -> str:
        payload = {
            "user_id": str(uuid4()),
            "email": "user@example.com",
            "name": "Regular User",
            "role": "user",
            "is_active": True,
            "expiration": (datetime.now() + timedelta(hours=1)).timestamp(),
            "issued_at": datetime.now().timestamp(),
            "type": "access",
            "referrer_id": None
        }
        return jwt.encode(payload, os.getenv("JWT_SECRET_KEY", "random_secret_key"), algorithm="HS256")
    
    @staticmethod
    def create_expired_token() -> str:
        payload = {
            "user_id": str(uuid4()),
            "email": "test@example.com",
            "name": "Test User",
            "role": "admin",
            "is_active": True,
            "expiration": (datetime.now() - timedelta(hours=1)).timestamp(),
            "issued_at": (datetime.now() - timedelta(hours=2)).timestamp(),
            "type": "access",
            "referrer_id": None
        }
        return jwt.encode(payload, os.getenv("JWT_SECRET_KEY", "random_secret_key"), algorithm="HS256")
    
    @pytest_asyncio.fixture
    async def client(self):
        with patch('cache.redis_client.RedisClient') as mock_redis_class:
            with patch('database.connection.PostgreSQLConnection') as mock_db_class:
                with patch('services.orders_grpc_client.PaymentGRPCClient') as mock_payment_class:
                    mock_redis_instance = MagicMock()
                    mock_redis_instance.ping = AsyncMock(return_value=True)
                    mock_redis_instance.get_pool = AsyncMock()
                    mock_redis_instance.get_client = AsyncMock()
                    mock_redis_instance.is_connected = True
                    mock_redis_class.return_value = mock_redis_instance
                    
                    mock_db_instance = MagicMock()
                    mock_db_instance.get_session = AsyncMock()
                    mock_db_instance.async_session_local = AsyncMock()
                    mock_db_class.return_value = mock_db_instance
                    
                    mock_payment_instance = AsyncMock()
                    mock_payment_response = MagicMock()
                    mock_payment_response.payment_id = f"payment_{uuid4().hex[:8]}"
                    mock_payment_response.client_secret = f"pi_secret_{uuid4().hex[:8]}"
                    mock_payment_response.checkout_url = f"https://checkout.stripe.com/pay/{uuid4().hex}"
                    
                    mock_payment_instance.create_payment = AsyncMock(return_value=mock_payment_response)
                    mock_payment_instance.get_payment = AsyncMock(return_value={
                        "id": f"payment_{uuid4().hex[:8]}",
                        "status": "succeeded",
                        "client_secret": f"pi_secret_{uuid4().hex[:8]}",
                        "checkout_url": f"https://checkout.stripe.com/pay/{uuid4().hex}"
                    })
                    mock_payment_instance.initialize = AsyncMock()
                    mock_payment_instance.close = AsyncMock()
                    mock_payment_class.return_value = mock_payment_instance
                    
                    with patch('cache.cache_service.cache_service') as mock_cache:
                        mock_cache_instance = MagicMock()
                        mock_cache_instance.enabled = True
                        mock_cache_instance.get_order = AsyncMock(return_value=None)
                        mock_cache_instance.set_order = AsyncMock(return_value=True)
                        mock_cache_instance.delete_user_orders = AsyncMock(return_value=0)
                        mock_cache.return_value = mock_cache_instance
                        
                        with patch('repositories.orders_repository.cache_service', mock_cache_instance):
                            from database.connection import get_db
                            
                            mock_session = AsyncMock()
                            
                            from repositories.orders_repository import OrderRepository
                            with patch.object(OrderRepository, '__init__', return_value=None):
                                mock_repo = MagicMock()
                                mock_order_instance = MagicMock()
                                mock_order_instance.id = uuid4()
                                mock_order_instance.status = "pending"
                                mock_order_instance.total = 1059.97
                                mock_order_instance.user_id = "30780061-1b7f-431d-8d9e-6382ac453160"
                                mock_order_instance.to_dict = Mock(return_value={
                                    "id": str(mock_order_instance.id),
                                    "status": "pending",
                                    "total": 1059.97,
                                    "items": [
                                        {"product_id": "prod_1", "name": "Laptop", "quantity": 1, "unit_price": 999.99},
                                        {"product_id": "prod_2", "name": "Mouse", "quantity": 2, "unit_price": 29.99}
                                    ],
                                    "user_id": "30780061-1b7f-431d-8d9e-6382ac453160",
                                    "created_at": "2024-01-01T00:00:00Z",
                                    "payment_id": f"payment_{uuid4().hex[:8]}",
                                    "checkout_url": f"https://checkout.stripe.com/pay/{uuid4().hex}"
                                })
                                
                                mock_repo.create_order = AsyncMock(return_value=mock_order_instance)
                                mock_repo.get_order_by_id = AsyncMock(return_value=mock_order_instance)
                                mock_repo.update_order_payment_id = AsyncMock()
                                mock_repo.update_order_status = AsyncMock()
                                mock_repo.update_order_checkout_url = AsyncMock()
                                mock_repo.update_order_receipt_url = AsyncMock()
                                mock_repo.list_orders = AsyncMock(return_value=[mock_order_instance.to_dict()])
                                mock_repo.count_orders = AsyncMock(return_value=1)
                                
                                OrderRepository.__init__ = Mock(return_value=None)
                                OrderRepository.create_order = mock_repo.create_order
                                OrderRepository.get_order_by_id = mock_repo.get_order_by_id
                                OrderRepository.update_order_payment_id = mock_repo.update_order_payment_id
                                OrderRepository.update_order_status = mock_repo.update_order_status
                                OrderRepository.update_order_checkout_url = mock_repo.update_order_checkout_url
                                OrderRepository.update_order_receipt_url = mock_repo.update_order_receipt_url
                                OrderRepository.list_orders = mock_repo.list_orders
                                OrderRepository.count_orders = mock_repo.count_orders
                                
                                async def mock_get_db():
                                    yield mock_session
                                
                                app.dependency_overrides[get_db] = lambda: mock_session
                                
                                async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                                    yield client
                                
                                app.dependency_overrides.clear()
    
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
        assert data["service"] == "order"
        assert "redis" in data

    @pytest.mark.asyncio
    async def test_ready_endpoint(self, client):
        response = await client.get("/ready")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "service" in data
        assert data["service"] == "order"

    @pytest.mark.asyncio
    async def test_info_endpoint(self, client):
        response = await client.get("/info")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "cache" in data
        assert "docs" in data
        assert "cache_health" in data

    @pytest.mark.asyncio
    async def test_cache_health_endpoint(self, client):
        response = await client.get("/cache/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "cache_enabled" in data

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
        assert response.status_code == 201
        
        data = response.json()
        assert "id" in data
        assert "status" in data
        assert "total" in data
        assert "items" in data
        assert "created_at" in data
        assert "client_secret" in data
        assert "checkout_url" in data
        assert data["status"] == "pending"
        assert isinstance(data["items"], list)

    @pytest.mark.asyncio
    async def test_create_order_contract_user(self, client, user_auth_header):
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
        assert response.status_code == 201
        
        data = response.json()
        assert "id" in data
        assert "status" in data
        assert "total" in data
        assert data["status"] == "pending"

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
        order_id = str(uuid4())
        response = await client.get(f"/{order_id}", headers=admin_auth_header)
        assert response.status_code == 200
        
        data = response.json()
        assert "id" in data
        assert "status" in data
        assert "total" in data
        assert "items" in data

    @pytest.mark.asyncio
    async def test_get_order_not_found_contract_admin(self, client, admin_auth_header):
        from repositories.orders_repository import OrderRepository
        OrderRepository.get_order_by_id = AsyncMock(return_value=None)
        
        order_id = str(uuid4())
        response = await client.get(f"/{order_id}", headers=admin_auth_header)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_expired_token(self, client, expired_auth_header):
        response = await client.get("/", headers=expired_auth_header)
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_missing_token(self, client):
        response = await client.get("/")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_order_empty_items(self, client, admin_auth_header):
        order_data = {
            "items": [],
            "billing_address_id": "addr_1",
            "shipping_address_id": "addr_1",
            "payment_method_token": "pm_tok_abc"
        }
        
        response = await client.post("/", json=order_data, headers=admin_auth_header)
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_create_order_missing_items(self, client, admin_auth_header):
        order_data = {
            "billing_address_id": "addr_1",
            "shipping_address_id": "addr_1",
            "payment_method_token": "pm_tok_abc"
        }
        
        response = await client.post("/", json=order_data, headers=admin_auth_header)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_payment_webhook_missing_api_key(self, client):
        webhook_data = {
            "order_id": str(uuid4()),
            "status": "succeeded",
            "receipt_url": "https://receipt.example.com/123"
        }
        
        response = await client.post("/webhooks/payment-updates", json=webhook_data)
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_payment_webhook_invalid_api_key(self, client):
        webhook_data = {
            "order_id": str(uuid4()),
            "status": "succeeded",
            "receipt_url": "https://receipt.example.com/123"
        }
        
        response = await client.post(
            "/webhooks/payment-updates", 
            json=webhook_data,
            headers={"X-API-Key": "invalid_key"}
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_list_orders_contract_user(self, client, user_auth_header):
        response = await client.get("/", headers=user_auth_header)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)

    @pytest.mark.asyncio
    async def test_routes_endpoint(self, client):
        response = await client.get("/routes")
        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert "total_routes" in data
        assert "routes" in data

    @pytest.mark.asyncio
    async def test_global_exception_handler(self, client, admin_auth_header):
        from repositories.orders_repository import OrderRepository
        OrderRepository.get_order_by_id = AsyncMock(side_effect=Exception("Test error"))
        
        response = await client.get(f"/{uuid4()}", headers=admin_auth_header)
        assert response.status_code == 500
        data = response.json()
        assert "type" in data
        assert "title" in data
        assert "status" in data
        assert data["status"] == 500


class TestOrderAPIErrorScenarios:
    
    @staticmethod
    def create_admin_token() -> str:
        payload = {
            "user_id": str(uuid4()),
            "email": "admin@example.com",
            "name": "Admin",
            "role": "admin",
            "is_active": True,
            "expiration": (datetime.now() + timedelta(hours=1)).timestamp(),
            "issued_at": datetime.now().timestamp(),
            "type": "access",
            "referrer_id": None
        }
        return jwt.encode(payload, os.getenv("JWT_SECRET_KEY", "random_secret_key"), algorithm="HS256")
    
    @pytest_asyncio.fixture
    async def client(self):
        with patch('cache.redis_client.RedisClient') as mock_redis_class:
            with patch('database.connection.PostgreSQLConnection') as mock_db_class:
                with patch('services.orders_grpc_client.PaymentGRPCClient') as mock_payment_class:
                    mock_redis_instance = MagicMock()
                    mock_redis_instance.ping = AsyncMock(return_value=True)
                    mock_redis_instance.get_pool = AsyncMock()
                    mock_redis_instance.get_client = AsyncMock()
                    mock_redis_instance.is_connected = True
                    mock_redis_class.return_value = mock_redis_instance
                    
                    mock_db_instance = MagicMock()
                    mock_db_instance.get_session = AsyncMock()
                    mock_db_instance.async_session_local = AsyncMock()
                    mock_db_class.return_value = mock_db_instance
                    
                    mock_payment_instance = AsyncMock()
                    mock_payment_response = MagicMock()
                    mock_payment_response.payment_id = f"payment_{uuid4().hex[:8]}"
                    mock_payment_response.client_secret = f"pi_secret_{uuid4().hex[:8]}"
                    mock_payment_response.checkout_url = f"https://checkout.stripe.com/pay/{uuid4().hex}"
                    
                    mock_payment_instance.create_payment = AsyncMock(return_value=mock_payment_response)
                    mock_payment_instance.initialize = AsyncMock()
                    mock_payment_instance.close = AsyncMock()
                    mock_payment_class.return_value = mock_payment_instance
                    
                    with patch('cache.cache_service.cache_service') as mock_cache:
                        mock_cache_instance = MagicMock()
                        mock_cache_instance.enabled = True
                        mock_cache_instance.get_order = AsyncMock(return_value=None)
                        mock_cache_instance.set_order = AsyncMock(return_value=True)
                        mock_cache.return_value = mock_cache_instance
                        
                        with patch('repositories.orders_repository.cache_service', mock_cache_instance):
                            from database.connection import get_db
                            
                            mock_session = AsyncMock()
                            mock_repo = AsyncMock()
                            
                            from repositories.orders_repository import OrderRepository
                            with patch.object(OrderRepository, '__init__', return_value=None):
                                mock_repo.create_order = AsyncMock()
                                mock_repo.get_order_by_id = AsyncMock(return_value=None)
                                mock_repo.list_orders = AsyncMock(return_value=[])
                                mock_repo.count_orders = AsyncMock(return_value=0)
                                
                                OrderRepository.__init__ = Mock(return_value=None)
                                OrderRepository.create_order = mock_repo.create_order
                                OrderRepository.get_order_by_id = mock_repo.get_order_by_id
                                OrderRepository.list_orders = mock_repo.list_orders
                                OrderRepository.count_orders = mock_repo.count_orders
                                
                                async def mock_get_db():
                                    yield mock_session
                                
                                app.dependency_overrides[get_db] = lambda: mock_session
                                
                                async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                                    yield client
                                
                                app.dependency_overrides.clear()
    
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
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_cors_headers_contract(self, client, admin_auth_header):
        response = await client.get("/health", headers={"Origin": "http://localhost:3000", **admin_auth_header})
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_invalid_token_format(self, client):
        response = await client.get("/", headers={"Authorization": "InvalidTokenFormat"})
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_missing_bearer_prefix(self, client):
        response = await client.get("/", headers={"Authorization": "test_token"})
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_order_invalid_uuid_format(self, client, admin_auth_header):
        response = await client.get("/invalid-uuid-format", headers=admin_auth_header)
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_create_order_negative_quantity(self, client, admin_auth_header):
        order_data = {
            "items": [
                {
                    "product_id": "prod_1",
                    "name": "Test Product",
                    "quantity": -1,
                    "unit_price": 50.00
                }
            ],
            "billing_address_id": "addr_1",
            "shipping_address_id": "addr_1",
            "payment_method_token": "pm_tok_abc"
        }
        
        response = await client.post("/", json=order_data, headers=admin_auth_header)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_order_negative_price(self, client, admin_auth_header):
        order_data = {
            "items": [
                {
                    "product_id": "prod_1",
                    "name": "Test Product",
                    "quantity": 1,
                    "unit_price": -50.00
                }
            ],
            "billing_address_id": "addr_1",
            "shipping_address_id": "addr_1",
            "payment_method_token": "pm_tok_abc"
        }
        
        response = await client.post("/", json=order_data, headers=admin_auth_header)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_list_orders_invalid_page(self, client, admin_auth_header):
        response = await client.get("/?page=0", headers=admin_auth_header)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_list_orders_invalid_page_size(self, client, admin_auth_header):
        response = await client.get("/?page_size=200", headers=admin_auth_header)
        assert response.status_code == 422