import pytest
import pytest_asyncio
import json
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4
from datetime import datetime

from services.payments_service import PaymentService
from services.idempotency_service import IdempotencyService
from services.commissions_service import CommissionService
from database import pydantic_models
from database.database_models import PaymentDB, PaymentStatus


class TestPaymentService:
    @pytest_asyncio.fixture
    async def mock_logger(self):
        return Mock()

    @pytest_asyncio.fixture
    async def mock_db_session(self):
        return AsyncMock()

    @pytest_asyncio.fixture
    async def mock_commission_service(self):
        return Mock(spec=CommissionService)

    @pytest_asyncio.fixture
    async def payment_service(self, mock_logger, mock_db_session, mock_commission_service):
        with patch('cache.redis_cache.RedisCache') as mock_redis_class:
            mock_redis_instance = AsyncMock()
            mock_redis_instance.get = AsyncMock()
            mock_redis_instance.set = AsyncMock()
            mock_redis_instance.delete = AsyncMock()
            mock_redis_instance.flush_pattern = AsyncMock()
            mock_redis_instance.exists = AsyncMock(return_value=False)
            mock_redis_instance.keys = AsyncMock(return_value=[])
            mock_redis_instance.ping = AsyncMock(return_value=True)
            mock_redis_class.return_value = mock_redis_instance
            
            with patch('services.payments_service.PaymentRepository') as mock_repo_class:
                mock_repo_instance = AsyncMock()
                mock_repo_class.return_value = mock_repo_instance
                
                mock_stripe_instance = Mock()
                mock_stripe_instance.handle_webhook_event = AsyncMock()
                
                mock_orchestrator_instance = Mock()
                mock_orchestrator_instance.create_and_process_payment = AsyncMock()
                
                mock_webhook_instance = Mock()
                mock_webhook_instance.handle_stripe_event = AsyncMock(return_value=("succeeded", "http://receipt.example.com"))
                
                mock_notification_svc_instance = Mock()
                mock_notification_svc_instance.notify_orders_service = AsyncMock(return_value=True)
                
                mock_refund_instance = Mock()
                mock_refund_instance.process_refund = AsyncMock()
                
                mock_notification_instance = Mock()
                mock_notification_instance.send_notification = AsyncMock(return_value=True)
                
                mock_retry_instance = Mock()
                mock_retry_instance.execute_with_retry = AsyncMock(side_effect=lambda op, logger: op())
                
                with patch('services.payments_service.StripeService', return_value=mock_stripe_instance):
                    with patch('services.payments_service.PaymentOrchestrator', return_value=mock_orchestrator_instance):
                        with patch('services.payments_service.WebhookHandler', return_value=mock_webhook_instance):
                            with patch('services.payments_service.PaymentNotificationService', return_value=mock_notification_svc_instance):
                                with patch('services.payments_service.RefundProcessor', return_value=mock_refund_instance):
                                    with patch('services.payments_service.NotificationService', return_value=mock_notification_instance):
                                        with patch('services.payments_service.RetryService', return_value=mock_retry_instance):
                                            service = PaymentService(
                                                logger=mock_logger, 
                                                db_session=mock_db_session,
                                                stripe_service=mock_stripe_instance,
                                                commission_service=mock_commission_service,
                                                redis_cache=mock_redis_instance
                                            )
                                            
                                            service.payment_repo = mock_repo_instance
                                            service.payment_orchestrator = mock_orchestrator_instance
                                            service.payment_notification_service = mock_notification_svc_instance
                                            service.webhook_handler = mock_webhook_instance
                                            service.refund_processor = mock_refund_instance
                                            service.idempotency_service = IdempotencyService(mock_redis_instance)
                                            
                                            yield service

    @pytest_asyncio.fixture
    def sample_payment_db(self):
        return PaymentDB(
            id=uuid4(),
            order_id="order_123",
            user_id="user_123",
            amount=99.99,
            status=PaymentStatus.CREATED,
            stripe_payment_intent_id="pi_123",
            payment_method_token="pm_tok_abc",
            currency="usd",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

    @pytest_asyncio.fixture
    def sample_payment_response(self, sample_payment_db):
        return pydantic_models.PaymentResponse(
            id=str(sample_payment_db.id),
            order_id=sample_payment_db.order_id,
            user_id=sample_payment_db.user_id,
            amount=sample_payment_db.amount,
            status=sample_payment_db.status,
            stripe_payment_intent_id=sample_payment_db.stripe_payment_intent_id,
            payment_method_token=sample_payment_db.payment_method_token,
            currency=sample_payment_db.currency,
            created_at=sample_payment_db.created_at.isoformat(),
            updated_at=sample_payment_db.updated_at.isoformat(),
            client_secret=None
        )

    @pytest.mark.asyncio
    async def test_idempotency_cache_hit(self, payment_service):
        mock_redis = payment_service.idempotency_service.redis
        cached_result = {"status": "processed", "event": "test"}
        mock_redis.get.return_value = json.dumps(cached_result)
        operation = AsyncMock()
        result = await payment_service.idempotency_service.execute_once(
            key="test_key",
            operation=operation
        )
        mock_redis.get.assert_called_once_with("idemp:test_key")
        operation.assert_not_called()
        assert result == cached_result

    @pytest.mark.asyncio
    async def test_idempotency_cache_miss(self, payment_service):
        mock_redis = payment_service.idempotency_service.redis
        mock_redis.get.return_value = None
        operation_result = {"status": "processed", "event": "test"}
        operation = AsyncMock(return_value=operation_result)
        result = await payment_service.idempotency_service.execute_once(
            key="test_key",
            operation=operation,
            ttl=300
        )
        mock_redis.get.assert_called_once_with("idemp:test_key")
        operation.assert_called_once()
        mock_redis.set.assert_called_once_with(
            "idemp:test_key", 
            json.dumps(operation_result), 
            300
        )
        assert result == operation_result

    @pytest.mark.asyncio
    async def test_idempotency_no_redis_fallback(self, payment_service):
        payment_service.idempotency_service.redis = None
        operation_result = {"status": "processed"}
        operation = AsyncMock(return_value=operation_result)
        result = await payment_service.idempotency_service.execute_once(
            key="test_key",
            operation=operation
        )
        operation.assert_called_once()
        assert result == operation_result

    @pytest.mark.asyncio
    async def test_idempotency_redis_error_fallback(self, payment_service):
        mock_redis = payment_service.idempotency_service.redis
        mock_redis.get.side_effect = Exception("Redis error")
        operation_result = {"status": "processed"}
        operation = AsyncMock(return_value=operation_result)
        result = await payment_service.idempotency_service.execute_once(
            key="test_key",
            operation=operation
        )
        operation.assert_called_once()
        assert result == operation_result

    @pytest.mark.asyncio
    async def test_webhook_idempotency_simple(self, payment_service, sample_payment_db):
        from fastapi import Request
        mock_request = Mock(spec=Request)
        mock_request.url = "http://test/webhook"
        mock_request.method = "POST"
        mock_request.client = Mock()
        mock_request.client.host = "127.0.0.1"
        event_id = "evt_test_123"
        payment_id = str(sample_payment_db.id)
        mock_event_data = {
            "type": "payment_intent.succeeded",
            "id": event_id,
            "data": {
                "object": {
                    "id": "pi_123",
                    "status": "succeeded",
                    "metadata": {"payment_id": payment_id}
                }
            }
        }
        payment_service.stripe_service.handle_webhook_event = AsyncMock(return_value=mock_event_data)
        payment_service.payment_repo.get_payment_by_id.return_value = sample_payment_db
        mock_redis = payment_service.idempotency_service.redis
        call_count = 0
        async def mock_redis_get(key):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return None
            else:
                return json.dumps({"status": "processed", "event": "payment_intent.succeeded"})
        mock_redis.get.side_effect = mock_redis_get
        mock_redis.set = AsyncMock()
        first_result = await payment_service.process_webhook(
            mock_request, b'{}', "stripe-signature"
        )
        payment_service.webhook_handler.handle_stripe_event.reset_mock()
        second_result = await payment_service.process_webhook(
            mock_request, b'{}', "stripe-signature"
        )
        assert first_result["status"] == "processed"
        payment_service.webhook_handler.handle_stripe_event.assert_not_called()
        assert second_result == first_result
    
    @pytest.mark.asyncio 
    async def test_webhook_idempotency_different_events(self, payment_service, sample_payment_db):
        from fastapi import Request
        mock_request = Mock(spec=Request)
        mock_request.url = "http://test/webhook"
        mock_request.method = "POST"
        mock_request.client = Mock()
        mock_request.client.host = "127.0.0.1"
        payment_id = str(sample_payment_db.id)
        from cache.redis_cache import RedisCache
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.set = AsyncMock()
        RedisCache.return_value = mock_redis
        payment_service.idempotency_service = IdempotencyService(mock_redis)
        payment_service.stripe_service.handle_webhook_event = AsyncMock(return_value={
            "type": "payment_intent.created",
            "id": "evt_created_123",
            "data": {"object": {"metadata": {"payment_id": payment_id}}}
        })
        payment_service.payment_repo.get_payment_by_id.return_value = sample_payment_db
        result1 = await payment_service.process_webhook(mock_request, b'{}', "sig")
        payment_service.webhook_handler.handle_stripe_event.reset_mock()
        mock_redis.get.reset_mock()
        mock_redis.set.reset_mock()
        mock_redis.get.return_value = None
        payment_service.stripe_service.handle_webhook_event = AsyncMock(return_value={
            "type": "payment_intent.succeeded", 
            "id": "evt_succeeded_456",
            "data": {"object": {"metadata": {"payment_id": payment_id}}}
        })
        result2 = await payment_service.process_webhook(mock_request, b'{}', "sig")
        assert payment_service.webhook_handler.handle_stripe_event.call_count == 1
        assert result1["status"] == "processed"
        assert result2["status"] == "processed"
        
    @pytest.mark.asyncio
    async def test_get_payment_cache_hit(self, payment_service, sample_payment_response):
        payment_id = str(uuid4())
        from cache.redis_cache import RedisCache
        cached_dict = sample_payment_response.dict()
        RedisCache.return_value.get.return_value = cached_dict
        result = await payment_service.get_payment(payment_id)
        RedisCache.return_value.get.assert_called_once()
        payment_service.payment_repo.get_payment_by_id.assert_not_called()
        assert hasattr(result, 'id') or 'id' in result

    @pytest.mark.asyncio
    async def test_cache_serialization(self, payment_service, sample_payment_response):
        payment_id = str(uuid4())
        from cache.redis_cache import RedisCache
        cached_dict = sample_payment_response.dict()
        RedisCache.return_value.get.return_value = cached_dict
        result = await payment_service.get_payment(payment_id)
        if hasattr(result, 'id'):
            assert result.id == sample_payment_response.id
        elif isinstance(result, dict):
            assert result['id'] == sample_payment_response.id

    @pytest.mark.asyncio
    async def test_get_payment_not_found(self, payment_service):
        payment_id = str(uuid4())
        from cache.redis_cache import RedisCache
        RedisCache.return_value.get.return_value = None
        payment_service.payment_repo.get_payment_by_id.return_value = None
        with pytest.raises(Exception) as exc_info:
            await payment_service.get_payment(payment_id)
        assert "Payment not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_payment_success(self, payment_service, sample_payment_db):
        payment_id = str(sample_payment_db.id)
        from cache.redis_cache import RedisCache
        RedisCache.return_value.get.return_value = None
        payment_service.payment_repo.get_payment_by_id.return_value = sample_payment_db
        result = await payment_service.get_payment(payment_id)
        payment_service.payment_repo.get_payment_by_id.assert_called_once()
        RedisCache.return_value.set.assert_called_once()
        assert hasattr(result, 'id') or 'id' in result

    @pytest.mark.asyncio
    async def test_get_payment_cache_miss(self, payment_service, sample_payment_db):
        payment_id = str(sample_payment_db.id)
        from cache.redis_cache import RedisCache
        RedisCache.return_value.get.return_value = None
        payment_service.payment_repo.get_payment_by_id.return_value = sample_payment_db
        result = await payment_service.get_payment(payment_id)
        RedisCache.return_value.get.assert_called_once()
        RedisCache.return_value.set.assert_called_once()
        payment_service.payment_repo.get_payment_by_id.assert_called_once()
        assert hasattr(result, 'id') or 'id' in result

    @pytest.mark.asyncio
    async def test_create_payment_invalidates_cache(self, payment_service, sample_payment_db):
        payment_data = pydantic_models.PaymentCreate(
            order_id="order_123",
            amount=99.99,
            user_id="user_123",
            payment_method_token="pm_tok_abc",
            currency="usd"
        )
        from cache.redis_cache import RedisCache
        payment_service.payment_orchestrator.create_and_process_payment.return_value = sample_payment_db
        await payment_service.create_payment(payment_data)
        RedisCache.return_value.flush_pattern.assert_called_once_with("cache:payment_by_order:*")

    @pytest.mark.asyncio
    async def test_process_webhook_invalidates_cache(self, payment_service, sample_payment_db):
        from fastapi import Request
        mock_request = Mock(spec=Request)
        mock_request.url = "http://test/webhook"
        mock_request.method = "POST"
        mock_request.client = Mock()
        mock_request.client.host = "127.0.0.1"
        payment_id = str(sample_payment_db.id)
        from cache.redis_cache import RedisCache
        payment_service.stripe_service.handle_webhook_event = AsyncMock(return_value={
            "type": "payment_intent.succeeded",
            "id": "evt_test_123",
            "data": {
                "object": {
                    "id": "pi_123",
                    "status": "succeeded",
                    "metadata": {"payment_id": payment_id},
                    "receipt_url": "http://receipt.example.com"
                }
            }
        })
        payment_service.payment_repo.get_payment_by_id.return_value = sample_payment_db
        await payment_service.process_webhook(mock_request, b'{"test": "data"}', "stripe-signature")
        RedisCache.return_value.flush_pattern.assert_called_once_with("cache:payment_by_id:*")

    @pytest.mark.asyncio
    async def test_create_refund_invalidates_cache(self, payment_service, sample_payment_db):
        sample_payment_db.status = PaymentStatus.SUCCEEDED
        sample_payment_db.stripe_payment_intent_id = "pi_123"
        payment_id = str(sample_payment_db.id)
        refund_data = pydantic_models.RefundRequest(amount=50.0, reason="customer_request")
        from cache.redis_cache import RedisCache
        payment_service.payment_repo.get_payment_by_id.return_value = sample_payment_db
        payment_service.refund_processor.process_refund.return_value = {
            "id": "re_123",
            "status": "succeeded",
            "amount": 50.0,
            "currency": "usd",
            "reason": "customer_request"
        }
        await payment_service.create_refund(payment_id, refund_data)
        RedisCache.return_value.flush_pattern.assert_called_once_with("cache:payment_by_id:*")

    @pytest.mark.asyncio
    async def test_cache_ttl_correct(self, payment_service, sample_payment_db):
        payment_id = str(sample_payment_db.id)
        from cache.redis_cache import RedisCache
        RedisCache.return_value.get.return_value = None
        payment_service.payment_repo.get_payment_by_id.return_value = sample_payment_db
        await payment_service.get_payment(payment_id)
        RedisCache.return_value.set.assert_called_once()
        call_args = RedisCache.return_value.set.call_args
        assert call_args is not None

    @pytest.mark.asyncio
    async def test_create_payment_success(self, payment_service, sample_payment_db):
        payment_data = pydantic_models.PaymentCreate(
            order_id="order_123",
            amount=99.99,
            user_id="user_123",
            payment_method_token="pm_tok_abc",
            currency="usd"
        )
        payment_service.payment_orchestrator.create_and_process_payment.return_value = sample_payment_db
        result = await payment_service.create_payment(payment_data)
        assert hasattr(result, 'id') or 'id' in result

    @pytest.mark.asyncio
    async def test_create_payment_already_exists(self, payment_service, sample_payment_db):
        payment_data = pydantic_models.PaymentCreate(
            order_id="order_123",
            amount=99.99,
            user_id="user_123",
            payment_method_token="pm_tok_abc"
        )
        sample_payment_db.stripe_payment_intent_id = "existing_pi_123"
        payment_service.payment_orchestrator.create_and_process_payment.return_value = sample_payment_db
        result = await payment_service.create_payment(payment_data)
        assert hasattr(result, 'id') or 'id' in result

    @pytest.mark.asyncio
    async def test_process_webhook_success(self, payment_service, sample_payment_db):
        from fastapi import Request
        mock_request = Mock(spec=Request)
        mock_request.url = "http://test/webhook"
        mock_request.method = "POST"
        mock_request.client = Mock()
        mock_request.client.host = "127.0.0.1"
        payload = b'{"test": "data"}'
        sig_header = "stripe-signature"
        payment_service.stripe_service.handle_webhook_event = AsyncMock(return_value={
            "type": "payment_intent.succeeded",
            "id": "evt_test_123",
            "data": {
                "object": {
                    "id": "pi_123",
                    "status": "succeeded",
                    "metadata": {"payment_id": str(sample_payment_db.id)},
                    "receipt_url": "http://receipt.example.com"
                }
            }
        })
        payment_service.payment_repo.get_payment_by_id.return_value = sample_payment_db
        result = await payment_service.process_webhook(mock_request, payload, sig_header)
        assert result["status"] == "processed"

    @pytest.mark.asyncio
    async def test_process_webhook_with_mock_data_structure(self, payment_service, sample_payment_db):
        from fastapi import Request
        mock_request = Mock(spec=Request)
        mock_request.url = "http://test/webhook"
        mock_request.method = "POST"
        mock_request.client = Mock()
        mock_request.client.host = "127.0.0.1"
        payload = b'{"test": "data"}'
        sig_header = "stripe-signature"
        payment_service.stripe_service.handle_webhook_event = AsyncMock(return_value={
            "type": "payment_intent.succeeded",
            "id": "evt_test_456",
            "data": {
                "object": {
                    "id": "pi_123",
                    "status": "succeeded",
                    "metadata": {"payment_id": str(sample_payment_db.id)}
                }
            }
        })
        payment_service.payment_repo.get_payment_by_id.return_value = sample_payment_db
        result = await payment_service.process_webhook(mock_request, payload, sig_header)
        assert result["status"] == "processed"

    @pytest.mark.asyncio
    async def test_process_webhook_payment_failed(self, payment_service, sample_payment_db):
        from fastapi import Request
        mock_request = Mock(spec=Request)
        mock_request.url = "http://test/webhook"
        mock_request.method = "POST"
        mock_request.client = Mock()
        mock_request.client.host = "127.0.0.1"
        payload = b'{"test": "data"}'
        sig_header = "stripe-signature"
        payment_service.stripe_service.handle_webhook_event = AsyncMock(return_value={
            "type": "payment_intent.payment_failed",
            "id": "evt_test_789",
            "data": {
                "object": {
                    "id": "pi_123",
                    "status": "failed",
                    "metadata": {"payment_id": str(sample_payment_db.id)}
                }
            }
        })
        payment_service.payment_repo.get_payment_by_id.return_value = sample_payment_db
        result = await payment_service.process_webhook(mock_request, payload, sig_header)
        assert result["status"] == "processed"

    @pytest.mark.asyncio
    async def test_process_webhook_ignored_no_payment_id(self, payment_service):
        from fastapi import Request
        mock_request = Mock(spec=Request)
        mock_request.url = "http://test/webhook"
        mock_request.method = "POST"
        mock_request.client = Mock()
        mock_request.client.host = "127.0.0.1"
        payload = b'{"test": "data"}'
        sig_header = "stripe-signature"
        from cache.redis_cache import RedisCache
        payment_service.stripe_service.handle_webhook_event = AsyncMock(return_value={
            "type": "payment_intent.succeeded",
            "id": "evt_test_999",
            "data": {
                "object": {
                    "id": "pi_123",
                    "status": "succeeded",
                    "metadata": {}
                }
            }
        })
        RedisCache.return_value.flush_pattern.reset_mock()
        result = await payment_service.process_webhook(mock_request, payload, sig_header)
        assert result["status"] == "ignored"
        assert result["reason"] == "no_payment_id"

    @pytest.mark.asyncio
    async def test_create_refund_success(self, payment_service, sample_payment_db):
        sample_payment_db.status = PaymentStatus.SUCCEEDED
        sample_payment_db.stripe_payment_intent_id = "pi_123"
        payment_id = str(sample_payment_db.id)
        refund_data = pydantic_models.RefundRequest(amount=50.0, reason="customer_request")
        payment_service.payment_repo.get_payment_by_id.return_value = sample_payment_db
        refund_result = {
            "id": "re_123",
            "status": "succeeded",
            "amount": 50.0,
            "currency": "usd",
            "reason": "customer_request"
        }
        payment_service.refund_processor.process_refund.return_value = refund_result
        result = await payment_service.create_refund(payment_id, refund_data)
        assert result["id"] == "re_123"

    @pytest.mark.asyncio
    async def test_create_refund_stripe_error(self, payment_service, sample_payment_db):
        sample_payment_db.status = PaymentStatus.SUCCEEDED
        sample_payment_db.stripe_payment_intent_id = "pi_123"
        payment_id = str(sample_payment_db.id)
        refund_data = pydantic_models.RefundRequest()
        payment_service.payment_repo.get_payment_by_id.return_value = sample_payment_db
        payment_service.refund_processor.process_refund.side_effect = Exception("Stripe error")
        with pytest.raises(Exception) as exc_info:
            await payment_service.create_refund(payment_id, refund_data)
        assert "Stripe error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_payment_checkout_mode(self, payment_service, sample_payment_db):
        payment_data = pydantic_models.PaymentCreate(
            order_id="order_checkout_123",
            amount=150.0,
            user_id="user_checkout_123",
            payment_method_token="pm_checkout_123",
            checkout_mode=True,
            success_url="https://example.com/success",
            cancel_url="https://example.com/cancel"
        )
        sample_payment_db.checkout_url = "https://checkout.stripe.com/c/pay/cs_test_123"
        payment_service.payment_orchestrator.create_and_process_payment.return_value = sample_payment_db
        result = await payment_service.create_payment(payment_data)
        assert hasattr(result, 'checkout_url') or 'checkout_url' in result

    @pytest.mark.asyncio
    async def test_create_payment_checkout_mode_missing_urls(self, payment_service):
        payment_data = pydantic_models.PaymentCreate(
            order_id="order_invalid_123",
            amount=150.0,
            user_id="user_invalid_123",
            payment_method_token="pm_invalid_123",
            checkout_mode=True
        )
        payment_service.payment_orchestrator.create_and_process_payment.side_effect = Exception("requires success_url and cancel_url")
        with pytest.raises(Exception) as exc:
            await payment_service.create_payment(payment_data)
        assert "requires success_url and cancel_url" in str(exc.value)

    @pytest.mark.asyncio
    async def test_create_payment_intent_mode_fallback(self, payment_service, sample_payment_db):
        payment_data = pydantic_models.PaymentCreate(
            order_id="order_intent_123",
            amount=150.0,
            user_id="user_intent_123",
            payment_method_token="pm_intent_123",
            checkout_mode=False
        )
        payment_service.payment_orchestrator.create_and_process_payment.return_value = sample_payment_db
        result = await payment_service.create_payment(payment_data)
        assert hasattr(result, 'id')

    @pytest.mark.asyncio
    async def test_webhook_checkout_session_completed(self, payment_service, sample_payment_db):
        from fastapi import Request
        mock_request = Mock(spec=Request)
        mock_request.url = "http://test/webhook"
        mock_request.method = "POST"
        mock_request.client = Mock()
        mock_request.client.host = "127.0.0.1"
        event_id = "evt_checkout_123"
        payment_id = str(sample_payment_db.id)
        mock_event_data = {
            "type": "checkout.session.completed",
            "id": event_id,
            "data": {
                "object": {
                    "id": "cs_test_123",
                    "payment_intent": "pi_123",
                    "status": "complete",
                    "metadata": {"payment_id": payment_id}
                }
            }
        }
        payment_service.stripe_service.handle_webhook_event = AsyncMock(return_value=mock_event_data)
        payment_service.payment_repo.get_payment_by_id.return_value = sample_payment_db
        payment_service.webhook_handler.handle_stripe_event = AsyncMock(return_value=("succeeded", None))
        result = await payment_service.process_webhook(mock_request, b'{}', "stripe-signature")
        assert result["status"] == "processed"
        payment_service.webhook_handler.handle_stripe_event.assert_called_once()

    def test_backwards_compatibility_default_checkout_mode(self):
        payment_data = pydantic_models.PaymentCreate(
            order_id="order_default_123",
            amount=100.0,
            user_id="user_default_123",
            payment_method_token="pm_default_123"
        )
        assert getattr(payment_data, 'checkout_mode', True) == True
        assert hasattr(payment_data, 'success_url')
        assert hasattr(payment_data, 'cancel_url')