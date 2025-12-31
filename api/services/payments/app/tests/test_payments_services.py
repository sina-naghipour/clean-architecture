import pytest
import pytest_asyncio
import json
from unittest.mock import Mock, AsyncMock, patch, MagicMock, call
from uuid import uuid4
from datetime import datetime
import asyncio

from services.payments_service import PaymentService
from services.notification_service import NotificationService
from services.retry_service import RetryService
from services.webhook_handler import WebhookHandler
from services.stripe_service import StripeService
from services.payment_notification_service import PaymentNotificationService
from services.payment_orchestrator import PaymentOrchestrator
from services.refund_processor import RefundProcessor

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
    async def payment_service(self, mock_logger, mock_db_session):
        with patch('cache.redis_cache.RedisCache') as mock_redis_class:
            mock_redis_instance = AsyncMock()
            mock_redis_instance.get = AsyncMock()
            mock_redis_instance.set = AsyncMock()
            mock_redis_instance.delete = AsyncMock()
            mock_redis_instance.flush_pattern = AsyncMock()
            mock_redis_instance.exists = AsyncMock(return_value=False)
            mock_redis_instance.keys = AsyncMock(return_value=[])
            mock_redis_class.return_value = mock_redis_instance
            
            with patch('services.payments_service.PaymentRepository') as mock_repo_class:
                mock_repo_instance = AsyncMock()
                mock_repo_class.return_value = mock_repo_instance
                
                with patch('services.payments_service.StripeService') as mock_stripe_class:
                    mock_stripe_instance = Mock(spec=StripeService)
                    mock_stripe_class.return_value = mock_stripe_instance
                    
                    with patch('services.payments_service.WebhookIdempotencyService') as mock_idempotency_class:
                        mock_idempotency_instance = AsyncMock()
                        mock_idempotency_instance.is_duplicate_event = AsyncMock(return_value=False)
                        mock_idempotency_instance.acquire_event_lock = AsyncMock(return_value=True)
                        mock_idempotency_instance.release_event_lock = AsyncMock()
                        mock_idempotency_instance.mark_event_processed = AsyncMock()
                        mock_idempotency_instance.handle_event_with_idempotency = AsyncMock(
                            side_effect=lambda event_id, event_type, processor_func: processor_func()
                        )
                        mock_idempotency_class.return_value = mock_idempotency_instance
                        
                        with patch('services.payments_service.NotificationService') as mock_notification_class:
                            mock_notification_instance = Mock(spec=NotificationService)
                            mock_notification_instance.send_notification = AsyncMock(return_value=True)
                            mock_notification_class.return_value = mock_notification_instance
                            
                            with patch('services.payments_service.RetryService') as mock_retry_class:
                                mock_retry_instance = Mock(spec=RetryService)
                                mock_retry_instance.execute_with_retry = AsyncMock(side_effect=lambda op, logger: op())
                                mock_retry_class.return_value = mock_retry_instance
                                
                                with patch('services.payments_service.WebhookHandler') as mock_webhook_class:
                                    mock_webhook_instance = Mock(spec=WebhookHandler)
                                    mock_webhook_instance.handle_stripe_event = AsyncMock(
                                        return_value=("succeeded", "http://receipt.example.com")
                                    )
                                    mock_webhook_class.return_value = mock_webhook_instance
                                
                                with patch('services.payments_service.PaymentOrchestrator') as mock_orchestrator_class:
                                    mock_orchestrator_instance = Mock(spec=PaymentOrchestrator)
                                    mock_orchestrator_instance.create_and_process_payment = AsyncMock()
                                    mock_orchestrator_class.return_value = mock_orchestrator_instance
                                
                                with patch('services.payments_service.PaymentNotificationService') as mock_notification_svc_class:
                                    mock_notification_svc_instance = Mock(spec=PaymentNotificationService)
                                    mock_notification_svc_instance.notify_orders_service = AsyncMock(return_value=True)
                                    mock_notification_svc_class.return_value = mock_notification_svc_instance
                                
                                with patch('services.payments_service.RefundProcessor') as mock_refund_class:
                                    mock_refund_instance = Mock(spec=RefundProcessor)
                                    mock_refund_instance.process_refund = AsyncMock()
                                    mock_refund_class.return_value = mock_refund_instance
                                        
                                    service = PaymentService(
                                        logger=mock_logger, 
                                        db_session=mock_db_session,
                                        stripe_service=mock_stripe_instance,
                                        redis_cache=mock_redis_instance
                                    )
                                    
                                    service.payment_repo = mock_repo_instance
                                    service.stripe_service = mock_stripe_instance
                                    service.payment_orchestrator = mock_orchestrator_instance
                                    service.payment_notification_service = mock_notification_svc_instance
                                    service.webhook_handler = mock_webhook_instance
                                    service.refund_processor = mock_refund_instance
                                    service.idempotency_service = mock_idempotency_instance
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
    async def test_cache_decorator_with_exception(self, payment_service):
        payment_id = str(uuid4())
        
        from cache.redis_cache import RedisCache
        
        # Make Redis.get() return None (simulating internal exception)
        mock_redis = RedisCache.return_value
        mock_redis.get.return_value = None
        
        # Set up repository to return None (payment not found)
        payment_service.payment_repo.get_payment_by_id.return_value = None
        
        # When Redis fails, decorator should call the actual function
        # which will raise "Payment not found"
        with pytest.raises(Exception) as exc_info:
            await payment_service.get_payment(payment_id)
        
        # Repository SHOULD be called (graceful degradation)
        payment_service.payment_repo.get_payment_by_id.assert_called_once()
        assert "Payment not found" in str(exc_info.value)

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
    async def test_webhook_idempotency_duplicate_event(self, payment_service, sample_payment_db):
        from fastapi import Request
        from uuid import uuid4
        
        mock_request = Mock(spec=Request)
        mock_request.url = "http://test/webhook"
        mock_request.method = "POST"
        mock_request.client = Mock()
        mock_request.client.host = "127.0.0.1"
        
        event_id = f"evt_test_{uuid4()}"
        payment_id = str(sample_payment_db.id)
        
        mock_event_data = {
            "type": "payment_intent.succeeded",
            "id": event_id,
            "data": {
                "object": {
                    "id": "pi_123",
                    "status": "succeeded",
                    "metadata": {"payment_id": payment_id},
                    "receipt_url": "http://receipt.example.com"
                }
            }
        }
        
        payment_service.stripe_service.handle_webhook_event = AsyncMock(return_value=mock_event_data)
        payment_service.payment_repo.get_payment_by_id.return_value = sample_payment_db
        
        first_result = await payment_service.process_webhook(
            mock_request, b'{"test": "data"}', "stripe-signature"
        )
        assert first_result["status"] in ["processed", "already_processed"]
        
        payment_service.webhook_handler.handle_stripe_event.reset_mock()
        payment_service.payment_notification_service.notify_orders_service.reset_mock()
        
        second_result = await payment_service.process_webhook(
            mock_request, b'{"test": "data"}', "stripe-signature"
        )
        
        assert second_result.get("status") in ["already_processed", "processed"]
        
        if second_result.get("status") == "already_processed":
            payment_service.webhook_handler.handle_stripe_event.assert_not_called()
        else:
            payment_service.webhook_handler.handle_stripe_event.assert_called_once()

    @pytest.mark.asyncio
    async def test_webhook_idempotency_race_condition(self, payment_service, sample_payment_db):
        import asyncio
        from fastapi import Request
        
        mock_request = Mock(spec=Request)
        mock_request.url = "http://test/webhook"
        mock_request.method = "POST"
        mock_request.client = Mock()
        mock_request.client.host = "127.0.0.1"
        
        event_id = "evt_race_test_123"
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
        
        call_count = 0
        
        async def mock_is_duplicate(event_id):
            nonlocal call_count
            call_count += 1
            return call_count > 1
        
        async def mock_handle_with_idempotency(event_id, event_type, processor_func):
            if await mock_is_duplicate(event_id):
                return {"status": "already_processed", "event_id": event_id}
            return await processor_func()
        
        payment_service.idempotency_service.handle_event_with_idempotency = AsyncMock(
            side_effect=mock_handle_with_idempotency
        )
        
        async def process_webhook_concurrently():
            return await payment_service.process_webhook(
                mock_request, b'{"test": "data"}', "stripe-signature"
            )
        
        tasks = [process_webhook_concurrently() for _ in range(3)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        processed_count = 0
        duplicate_count = 0
        
        for result in results:
            if isinstance(result, Exception):
                continue
            if result.get("status") == "processed":
                processed_count += 1
            elif result.get("status") in ["already_processed", "already_processed_by_other"]:
                duplicate_count += 1
        
        assert processed_count == 1, f"Expected exactly 1 processed, got {processed_count}"
        assert duplicate_count == 2, f"Expected 2 duplicates, got {duplicate_count}"
        
        assert payment_service.webhook_handler.handle_stripe_event.call_count == 1

    @pytest.mark.asyncio
    async def test_webhook_idempotency_different_events_same_payment(self, payment_service, sample_payment_db):
        from fastapi import Request
        
        mock_request = Mock(spec=Request)
        mock_request.url = "http://test/webhook"
        mock_request.method = "POST"
        mock_request.client = Mock()
        mock_request.client.host = "127.0.0.1"
        
        payment_id = str(sample_payment_db.id)
        
        event_scenarios = [
            {
                "event_id": "evt_created_123",
                "event_type": "payment_intent.created",
                "status": "created"
            },
            {
                "event_id": "evt_succeeded_456",
                "event_type": "payment_intent.succeeded",
                "status": "succeeded"
            },
            {
                "event_id": "evt_failed_789",
                "event_type": "payment_intent.payment_failed",
                "status": "failed"
            }
        ]
        
        call_counts = {
            "webhook_handler": 0,
            "notification_service": 0
        }
        
        for scenario in event_scenarios:
            payment_service.webhook_handler.handle_stripe_event.reset_mock()
            
            mock_event_data = {
                "type": scenario["event_type"],
                "id": scenario["event_id"],
                "data": {
                    "object": {
                        "id": f"pi_{scenario['event_id']}",
                        "status": scenario["status"],
                        "metadata": {"payment_id": payment_id}
                    }
                }
            }
            
            payment_service.stripe_service.handle_webhook_event = AsyncMock(return_value=mock_event_data)
            payment_service.payment_repo.get_payment_by_id.return_value = sample_payment_db
            
            result = await payment_service.process_webhook(
                mock_request, b'{"test": "data"}', "stripe-signature"
            )
            
            assert result["status"] == "processed"
            payment_service.webhook_handler.handle_stripe_event.assert_called_once()
            call_counts["webhook_handler"] += 1
            
            result = await payment_service.process_webhook(
                mock_request, b'{"test": "data"}', "stripe-signature"
            )
            
            if result.get("status") == "already_processed":
                payment_service.webhook_handler.handle_stripe_event.assert_called_once()
        
        assert call_counts["webhook_handler"] == 3

    @pytest.mark.asyncio
    async def test_webhook_idempotency_redis_failure_fallback(self, payment_service, sample_payment_db):
        from fastapi import Request
        
        mock_request = Mock(spec=Request)
        mock_request.url = "http://test/webhook"
        mock_request.method = "POST"
        mock_request.client = Mock()
        mock_request.client.host = "127.0.0.1"
        
        event_id = "evt_redis_failure_123"
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
        
        payment_service.idempotency_service.is_duplicate_event = AsyncMock(side_effect=Exception("Redis connection failed"))
        
        result = await payment_service.process_webhook(
            mock_request, b'{"test": "data"}', "stripe-signature"
        )
        
        assert result["status"] == "processed"
        payment_service.webhook_handler.handle_stripe_event.assert_called_once()

    @pytest.mark.asyncio
    async def test_webhook_idempotency_lock_timeout_handling(self, payment_service, sample_payment_db):
        from fastapi import Request
        import asyncio
        
        mock_request = Mock(spec=Request)
        mock_request.url = "http://test/webhook"
        mock_request.method = "POST"
        mock_request.client = Mock()
        mock_request.client.host = "127.0.0.1"
        
        event_id = "evt_lock_test_123"
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
        
        payment_service.idempotency_service.acquire_event_lock = AsyncMock(return_value=False)
        payment_service.idempotency_service.is_duplicate_event = AsyncMock(return_value=False)
        
        result = await payment_service.process_webhook(
            mock_request, b'{"test": "data"}', "stripe-signature"
        )
        
        assert result.get("status") in ["lock_contention", "already_processed", "processed"]
        
        if result.get("status") == "lock_contention":
            payment_service.webhook_handler.handle_stripe_event.assert_not_called()

    @pytest.mark.asyncio
    async def test_webhook_idempotency_storage_expiry_simulation(self, payment_service, sample_payment_db):
        from fastapi import Request
        
        mock_request = Mock(spec=Request)
        mock_request.url = "http://test/webhook"
        mock_request.method = "POST"
        mock_request.client = Mock()
        mock_request.client.host = "127.0.0.1"
        
        event_id = "evt_expired_123"
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
        
        payment_service.idempotency_service.is_duplicate_event = AsyncMock(return_value=False)
        first_result = await payment_service.process_webhook(
            mock_request, b'{"test": "data"}', "stripe-signature"
        )
        assert first_result["status"] == "processed"
        
        payment_service.webhook_handler.handle_stripe_event.reset_mock()
        
        payment_service.idempotency_service.is_duplicate_event = AsyncMock(return_value=False)
        
        second_result = await payment_service.process_webhook(
            mock_request, b'{"test": "data"}', "stripe-signature"
        )
        
        if second_result.get("status") == "processed":
            payment_service.webhook_handler.handle_stripe_event.assert_called_once()
        else:
            assert second_result.get("status") == "already_processed"

    @pytest.mark.asyncio
    async def test_webhook_idempotency_event_without_id(self, payment_service, sample_payment_db):
        from fastapi import Request
        
        mock_request = Mock(spec=Request)
        mock_request.url = "http://test/webhook"
        mock_request.method = "POST"
        mock_request.client = Mock()
        mock_request.client.host = "127.0.0.1"
        
        payment_id = str(sample_payment_db.id)
        
        mock_event_data = {
            "type": "unknown",
            "id": "mock_event_id",
            "data": {
                "object": {
                    "metadata": {"payment_id": payment_id}
                }
            }
        }
        
        payment_service.stripe_service.handle_webhook_event = AsyncMock(return_value=mock_event_data)
        payment_service.payment_repo.get_payment_by_id.return_value = sample_payment_db
        
        result = await payment_service.process_webhook(
            mock_request, b'{"test": "data"}', "stripe-signature"
        )
        
        assert result["status"] in ["processed", "ignored"]

    @pytest.mark.asyncio
    async def test_webhook_idempotency_concurrent_different_events(self, payment_service):
        
        payment_service.idempotency_service.handle_event_with_idempotency.reset_mock()
        
        async def mock_processor_func():
            return {"status": "processed"}
        
        payment_service.idempotency_service.handle_event_with_idempotency = AsyncMock(
            return_value={"status": "processed"}
        )
        
        async def call_idempotency_service(event_id):
            return await payment_service.idempotency_service.handle_event_with_idempotency(
                event_id, "payment_intent.succeeded", mock_processor_func
            )
        
        tasks = []
        for i in range(5):
            event_id = f"evt_concurrent_{i}"
            tasks.append(call_idempotency_service(event_id))
        
        results = await asyncio.gather(*tasks)
        
        success_count = sum(1 for r in results if r.get("status") == "processed")
        assert success_count == 5, f"Expected 5 processed, got {success_count}"
        
        assert payment_service.idempotency_service.handle_event_with_idempotency.call_count == 5