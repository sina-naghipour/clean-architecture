import pytest
import pytest_asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from uuid import uuid4
from datetime import datetime

# Update imports to match the new structure
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
        with patch('services.payments_service.PaymentRepository') as mock_repo_class:
            mock_repo_instance = AsyncMock()
            mock_repo_class.return_value = mock_repo_instance
            
            with patch('services.payments_service.StripeService') as mock_stripe_class:
                mock_stripe_instance = Mock(spec=StripeService)
                mock_stripe_class.return_value = mock_stripe_instance
                
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
                            # FIX: Now returns a tuple (result, receipt_url)
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
                                stripe_service=mock_stripe_instance
                            )
                            
                            # Set up the mocked dependencies
                            service.payment_repo = mock_repo_instance
                            service.stripe_service = mock_stripe_instance
                            service.payment_orchestrator = mock_orchestrator_instance
                            service.payment_notification_service = mock_notification_svc_instance
                            service.webhook_handler = mock_webhook_instance
                            service.refund_processor = mock_refund_instance
                            
                            yield service
                            
                            if hasattr(service, 'http_client'):
                                await service.http_client.aclose()

    @pytest_asyncio.fixture
    def sample_payment_db(self):
        payment = PaymentDB(
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
        return payment

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

        assert isinstance(result, pydantic_models.PaymentResponse)
        assert result.id == str(sample_payment_db.id)

    @pytest.mark.asyncio
    async def test_create_payment_already_exists(self, payment_service, sample_payment_db):
        payment_data = pydantic_models.PaymentCreate(
            order_id="order_123",
            amount=99.99,
            user_id="user_123",
            payment_method_token="pm_tok_abc"
        )
        
        # Simulate existing payment
        sample_payment_db.stripe_payment_intent_id = "existing_pi_123"
        payment_service.payment_orchestrator.create_and_process_payment.return_value = sample_payment_db
        
        result = await payment_service.create_payment(payment_data)
        
        assert isinstance(result, pydantic_models.PaymentResponse)
        assert result.id == str(sample_payment_db.id)

    @pytest.mark.asyncio
    async def test_get_payment_success(self, payment_service, sample_payment_db):
        payment_id = str(sample_payment_db.id)
        
        payment_service.payment_repo.get_payment_by_id.return_value = sample_payment_db

        result = await payment_service.get_payment(payment_id)

        assert isinstance(result, pydantic_models.PaymentResponse)
        assert result.id == payment_id

    @pytest.mark.asyncio
    async def test_get_payment_not_found(self, payment_service):
        payment_id = str(uuid4())
        
        payment_service.payment_repo.get_payment_by_id.return_value = None
        
        with pytest.raises(Exception) as exc_info:
            await payment_service.get_payment(payment_id)
        
        assert "Payment not found" in str(exc_info.value)

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
        
        async def mock_handle_webhook_event(*args, **kwargs):
            return {
                "type": "payment_intent.succeeded",
                "data": {
                    "object": {
                        "id": "pi_123",
                        "status": "succeeded",
                        "metadata": {"payment_id": str(sample_payment_db.id)},
                        "receipt_url": "http://receipt.example.com"
                    }
                }
            }
        
        payment_service.stripe_service.handle_webhook_event = AsyncMock(side_effect=mock_handle_webhook_event)
        payment_service.payment_repo.get_payment_by_id.return_value = sample_payment_db
        
        # Webhook handler returns a tuple (result, receipt_url)
        payment_service.webhook_handler.handle_stripe_event.return_value = ("succeeded", "http://receipt.example.com")
        
        result = await payment_service.process_webhook(mock_request, payload, sig_header)

        assert "status" in result
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
        
        async def mock_handle_webhook_event(*args, **kwargs):
            return {
                "type": "payment_intent.succeeded",
                "data": {
                    "object": {
                        "id": "pi_123",
                        "status": "succeeded",
                        "metadata": {"payment_id": str(sample_payment_db.id)}
                    }
                }
            }
        
        payment_service.stripe_service.handle_webhook_event = AsyncMock(side_effect=mock_handle_webhook_event)
        payment_service.payment_repo.get_payment_by_id.return_value = sample_payment_db
        
        # Webhook handler returns a tuple (result, receipt_url)
        payment_service.webhook_handler.handle_stripe_event.return_value = ("succeeded", None)
        
        result = await payment_service.process_webhook(mock_request, payload, sig_header)

        assert "status" in result
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
        
        async def mock_handle_webhook_event(*args, **kwargs):
            return {
                "type": "payment_intent.payment_failed",
                "data": {
                    "object": {
                        "id": "pi_123",
                        "status": "failed",
                        "metadata": {"payment_id": str(sample_payment_db.id)}
                    }
                }
            }
        
        payment_service.stripe_service.handle_webhook_event = AsyncMock(side_effect=mock_handle_webhook_event)
        payment_service.payment_repo.get_payment_by_id.return_value = sample_payment_db
        
        # Webhook handler returns a tuple (result, receipt_url)
        payment_service.webhook_handler.handle_stripe_event.return_value = ("failed", None)
        
        result = await payment_service.process_webhook(mock_request, payload, sig_header)

        assert "status" in result
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
        
        async def mock_handle_webhook_event(*args, **kwargs):
            return {
                "type": "payment_intent.succeeded",
                "data": {
                    "object": {
                        "id": "pi_123",
                        "status": "succeeded",
                        "metadata": {}  # No payment_id
                    }
                }
            }
        
        payment_service.stripe_service.handle_webhook_event = AsyncMock(side_effect=mock_handle_webhook_event)
        
        result = await payment_service.process_webhook(mock_request, payload, sig_header)

        assert "status" in result
        assert result["status"] == "ignored"  # FIXED: Changed from "processed" to "ignored"
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

        assert "id" in result
        assert result["id"] == "re_123"

    @pytest.mark.asyncio
    async def test_create_refund_stripe_error(self, payment_service, sample_payment_db):
        sample_payment_db.status = PaymentStatus.SUCCEEDED
        sample_payment_db.stripe_payment_intent_id = "pi_123"
        
        payment_id = str(sample_payment_db.id)
        refund_data = pydantic_models.RefundRequest()
        
        payment_service.payment_repo.get_payment_by_id.return_value = sample_payment_db
        
        async def mock_process_refund_fail(*args, **kwargs):
            raise Exception("Stripe error")
        
        payment_service.refund_processor.process_refund = AsyncMock(side_effect=mock_process_refund_fail)
        
        with pytest.raises(Exception) as exc_info:
            await payment_service.create_refund(payment_id, refund_data)
        
        assert "Stripe error" in str(exc_info.value)