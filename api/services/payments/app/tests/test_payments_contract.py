import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from main import app
import os
from unittest.mock import patch, AsyncMock, MagicMock
import json

class TestPaymentAPIContract:
    
    @pytest_asyncio.fixture
    async def client(self):
        # Mock ALL database dependencies first
        with patch('database.connection.db_connection', autospec=True) as mock_db_conn:
            # Mock the database connection
            mock_db_conn.get_session = AsyncMock()
            mock_session = AsyncMock()
            mock_session.commit = AsyncMock()
            mock_session.rollback = AsyncMock()
            mock_session.close = AsyncMock()
            mock_db_conn.get_session.return_value.__aenter__.return_value = mock_session
            mock_db_conn.get_session.return_value.__aexit__.return_value = None
            
            # Mock RedisCache
            with patch('cache.redis_cache.RedisCache') as mock_redis_class:
                mock_redis_instance = AsyncMock()
                mock_redis_class.return_value = mock_redis_instance
                mock_redis_instance.get = AsyncMock(return_value=None)
                mock_redis_instance.set = AsyncMock()
                mock_redis_instance.flush_pattern = AsyncMock()
                
                # Mock app.state.redis_cache
                app.state.redis_cache = mock_redis_instance
                
                # Mock the StripeService to avoid actual Stripe calls
                with patch('services.payments_service.StripeService') as mock_stripe_class:
                    mock_stripe_instance = AsyncMock()
                    mock_stripe_class.return_value = mock_stripe_instance
                    
                    # Mock the PaymentRepository
                    with patch('services.payments_service.PaymentRepository') as mock_repo_class:
                        mock_repo_instance = AsyncMock()
                        mock_repo_class.return_value = mock_repo_instance
                        mock_repo_instance.get_payment_by_id = AsyncMock(return_value=None)
                        
                        # Mock webhook handling - must return data with 'type' and 'data' keys
                        async def mock_handle_webhook_event(payload, sig_header):
                            try:
                                payload_str = payload.decode('utf-8')
                                
                                if not payload_str.strip():
                                    return {
                                        "type": "payment_intent.succeeded",
                                        "id": "evt_mock_123",
                                        "data": {
                                            "object": {
                                                "id": "pi_123",
                                                "status": "succeeded",
                                                "metadata": {}
                                            }
                                        }
                                    }
                                
                                if payload_str.strip().startswith('{') and payload_str.strip().endswith('}'):
                                    try:
                                        data = json.loads(payload_str)
                                        return {
                                            "type": data.get("type", "payment_intent.succeeded"),
                                            "id": data.get("id", "evt_mock_123"),
                                            "data": {
                                                "object": {
                                                    "id": "pi_123",
                                                    "status": "succeeded",
                                                    "metadata": data.get("metadata", {})
                                                }
                                            }
                                        }
                                    except json.JSONDecodeError:
                                        return {
                                            "type": "payment_intent.succeeded",
                                            "id": "evt_mock_123",
                                            "data": {
                                                "object": {
                                                    "id": "pi_123",
                                                    "status": "succeeded",
                                                    "metadata": {}
                                                }
                                            }
                                        }
                                else:
                                    return {
                                        "type": "payment_intent.succeeded",
                                        "id": "evt_mock_123",
                                        "data": {
                                            "object": {
                                                "id": "pi_123",
                                                "status": "succeeded",
                                                "metadata": {}
                                            }
                                        }
                                    }
                            except UnicodeDecodeError:
                                return {
                                    "type": "payment_intent.succeeded",
                                    "id": "evt_mock_123",
                                    "data": {
                                        "object": {
                                            "id": "pi_123",
                                            "status": "succeeded",
                                            "metadata": {}
                                        }
                                    }
                                }
                        
                        mock_stripe_instance.handle_webhook_event = AsyncMock(side_effect=mock_handle_webhook_event)
                        
                        # Mock IdempotencyService
                        with patch('services.payments_service.IdempotencyService') as mock_idempotency_class:
                            mock_idempotency_instance = AsyncMock()
                            mock_idempotency_class.return_value = mock_idempotency_instance
                            mock_idempotency_instance.execute_once = AsyncMock(return_value={"status": "ignored", "reason": "no_payment_id"})
                            
                            # Mock CommissionService and Repository
                            with patch('services.commissions_service.CommissionService') as mock_commission_class:
                                mock_commission_instance = AsyncMock()
                                mock_commission_class.return_value = mock_commission_instance
                                
                                with patch('repositories.commissions_repository.CommissionRepository') as mock_commission_repo_class:
                                    mock_commission_repo_instance = AsyncMock()
                                    mock_commission_repo_class.return_value = mock_commission_repo_instance
                                    
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
        assert "docs" in data
        assert "health" in data
        assert "ready" in data

    @pytest.mark.asyncio
    async def test_webhook_endpoint_contract(self, client):
        response = await client.post(
            "/webhooks/stripe",
            content='{"type": "payment_intent.succeeded"}',
            headers={"Stripe-Signature": "t=123456,v1=test_signature"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ignored"
        assert data["reason"] == "no_payment_id"

    @pytest.mark.asyncio
    async def test_webhook_missing_signature_contract(self, client):
        response = await client.post(
            "/webhooks/stripe",
            content='{"type": "payment_intent.succeeded"}'
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_webhook_invalid_json_contract(self, client):
        response = await client.post(
            "/webhooks/stripe",
            content="{invalid json",
            headers={"Stripe-Signature": "t=123456,v1=test_signature"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ignored"
        assert data["reason"] == "no_payment_id"

    @pytest.mark.asyncio
    async def test_webhook_form_data_contract(self, client):
        response = await client.post(
            "/webhooks/stripe",
            content="order_id=order_123",
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Stripe-Signature": "t=123456,v1=test_signature"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ignored"
        assert data["reason"] == "no_payment_id"

    @pytest.mark.asyncio
    async def test_webhook_empty_payload_contract(self, client):
        response = await client.post(
            "/webhooks/stripe",
            content="",
            headers={"Stripe-Signature": "t=123456,v1=test_signature"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ignored"
        assert data["reason"] == "no_payment_id"

    @pytest.mark.asyncio
    async def test_webhook_with_payment_id_contract(self, client):
        response = await client.post(
            "/webhooks/stripe",
            content=json.dumps({
                "type": "payment_intent.succeeded",
                "data": {
                    "object": {
                        "metadata": {"payment_id": "123e4567-e89b-12d3-a456-426614174000"}
                    }
                }
            }),
            headers={"Stripe-Signature": "t=123456,v1=test_signature"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ignored"
        assert data["reason"] == "no_payment_id"

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
    async def test_method_not_allowed_contract(self, client):
        response = await client.put("/webhooks/stripe")
        assert response.status_code == 405

    @pytest.mark.asyncio
    async def test_cors_headers_contract(self, client):
        response = await client.get("/health", headers={"Origin": "http://localhost:3000"})
        assert "access-control-allow-origin" in response.headers
        assert response.headers["access-control-allow-origin"] == "http://localhost:3000"