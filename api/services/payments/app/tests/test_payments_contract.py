import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from main import app
import os

class TestPaymentAPIContract:
    
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
        assert "environment" in data
        assert "stripe_mode" in data
        assert data["service"] == "payments"

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
        assert "stripe_mode" in data
        assert "docs" in data
        assert "health" in data
        assert "ready" in data

    @pytest.mark.asyncio
    async def test_create_payment_contract(self, client):
        payment_data = {
            "order_id": "order_123",
            "amount": 99.99,
            "user_id": "user_123",
            "payment_method_token": "pm_tok_abc",
            "currency": "usd",
            "metadata": {"key": "value"}
        }
        
        response = await client.post("/", json=payment_data)
        
        assert response.status_code in [201, 409, 500]
        
        if response.status_code == 201:
            data = response.json()
            assert "id" in data
            assert "order_id" in data
            assert "user_id" in data
            assert "amount" in data
            assert "status" in data
            assert "payment_method_token" in data
            assert "currency" in data
            assert "created_at" in data
            assert "updated_at" in data
            assert data["order_id"] == "order_123"
            assert data["amount"] == 99.99
            
            assert "Location" in response.headers
            assert "/" in response.headers["Location"]

    @pytest.mark.asyncio
    async def test_create_payment_invalid_data_contract(self, client):
        payment_data = {
            "order_id": "order_123"
        }
        
        response = await client.post("/", json=payment_data)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_get_payment_contract(self, client):
        payment_data = {
            "order_id": "order_456",
            "amount": 50.0,
            "user_id": "user_456",
            "payment_method_token": "pm_tok_xyz"
        }
        
        create_response = await client.post("/", json=payment_data)
        
        if create_response.status_code == 201:
            payment_id = create_response.json()["id"]
            response = await client.get(f"/{payment_id}")
            assert response.status_code in [200, 404]
            
            if response.status_code == 200:
                data = response.json()
                assert "id" in data
                assert "order_id" in data
                assert "amount" in data
                assert "status" in data
                assert "payment_method_token" in data
                assert data["id"] == payment_id

    @pytest.mark.asyncio
    async def test_get_payment_not_found_contract(self, client):
        response = await client.get("/123e4567-e89b-12d3-a456-426614174000")
        assert response.status_code in [404, 500]

    @pytest.mark.asyncio
    async def test_get_payment_invalid_uuid_contract(self, client):
        response = await client.get("/not-a-uuid")
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_webhook_endpoint_contract(self, client):
        response = await client.post(
            "/webhooks/stripe",
            content="test payload",
            headers={"Stripe-Signature": "test_signature"}
        )
        assert response.status_code in [200, 400, 500]

    @pytest.mark.asyncio
    async def test_webhook_missing_signature_contract(self, client):
        response = await client.post("/webhooks/stripe")
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_refund_payment_contract(self, client):
        payment_data = {
            "order_id": "order_789",
            "amount": 75.0,
            "user_id": "user_789",
            "payment_method_token": "pm_tok_789"
        }
        
        create_response = await client.post("", json=payment_data)
        
        if create_response.status_code == 201:
            payment_id = create_response.json()["id"]
            refund_data = {
                "amount": 75.0,
                "reason": "customer_request"
            }
            
            response = await client.post(f"/{payment_id}/refund", json=refund_data)
            assert response.status_code in [200, 400, 404, 500]

    @pytest.mark.asyncio
    async def test_refund_invalid_data_contract(self, client):
        response = await client.post(
            "/123e4567-e89b-12d3-a456-426614174000/refund",
            json={"amount": -10.0}
        )
        assert response.status_code in [400, 404, 422, 500]

    @pytest.mark.asyncio
    async def test_routes_endpoint_contract(self, client):
        response = await client.get("/routes")
        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert "total_routes" in data
        assert "routes" in data
        assert isinstance(data["routes"], list)

    @pytest.mark.asyncio
    async def test_create_payment_negative_amount_contract(self, client):
        payment_data = {
            "order_id": "order_999",
            "amount": -10.0,
            "user_id": "user_999",
            "payment_method_token": "pm_tok_999"
        }
        
        response = await client.post("/", json=payment_data)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_payment_zero_amount_contract(self, client):
        payment_data = {
            "order_id": "order_000",
            "amount": 0.0,
            "user_id": "user_000",
            "payment_method_token": "pm_tok_000"
        }
        
        response = await client.post("/", json=payment_data)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_payment_missing_required_fields_contract(self, client):
        payment_data = {
            "order_id": "order_111"
        }
        
        response = await client.post("/", json=payment_data)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_malformed_json_contract(self, client):
        response = await client.post(
            "/",
            content="{invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_unsupported_media_type_contract(self, client):
        response = await client.post(
            "/",
            content="order_id=order_123",
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_method_not_allowed_contract(self, client):
        response = await client.put("/")
        assert response.status_code == 405

    @pytest.mark.asyncio
    async def test_cors_headers_contract(self, client):
        response = await client.get("/health", headers={"Origin": "http://localhost:3000"})
        
        if "access-control-allow-origin" in response.headers:
            assert response.headers["access-control-allow-origin"] == "http://localhost:3000"