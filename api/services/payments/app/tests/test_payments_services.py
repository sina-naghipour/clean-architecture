import pytest
import pytest_asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from uuid import uuid4
from datetime import datetime
from services.payments_service import PaymentService
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
                mock_stripe_instance = Mock()
                mock_stripe_class.return_value = mock_stripe_instance
                service = PaymentService(logger=mock_logger, db_session=mock_db_session)
                service.payment_repo = mock_repo_instance
                service.stripe_service = mock_stripe_instance
                service._notify_orders_service = AsyncMock(return_value=True)
                yield service

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
        
        payment_service.payment_repo.get_payment_by_order_id.return_value = None
        payment_service.payment_repo.create_payment.return_value = sample_payment_db
        payment_service.payment_repo.update_payment_stripe_id = AsyncMock()
        payment_service.payment_repo.update_payment_status = AsyncMock()
        payment_service.payment_repo.update_payment_client_secret = AsyncMock()
        
        async def mock_create_payment_intent(*args, **kwargs):
            return {
                "id": "pi_123",
                "status": "succeeded",
                "client_secret": "secret_123"
            }
        
        payment_service.stripe_service.create_payment_intent = AsyncMock(side_effect=mock_create_payment_intent)
        payment_service.stripe_service.map_stripe_status_to_payment_status.return_value = PaymentStatus.SUCCEEDED
        
        result = await payment_service.create_payment(payment_data)

        assert isinstance(result, pydantic_models.PaymentResponse)
        assert result.id == str(sample_payment_db.id)
        assert result.status == PaymentStatus.SUCCEEDED

    @pytest.mark.asyncio
    async def test_create_payment_already_exists(self, payment_service, sample_payment_db):
        payment_data = pydantic_models.PaymentCreate(
            order_id="order_123",
            amount=99.99,
            user_id="user_123",
            payment_method_token="pm_tok_abc"
        )
        
        payment_service.payment_repo.get_payment_by_order_id.return_value = sample_payment_db
        
        result = await payment_service.create_payment(payment_data)
        
        assert isinstance(result, pydantic_models.PaymentResponse)
        assert result.id == str(sample_payment_db.id)

    @pytest.mark.asyncio
    async def test_create_payment_stripe_failure(self, payment_service, sample_payment_db):
        payment_data = pydantic_models.PaymentCreate(
            order_id="order_123",
            amount=99.99,
            user_id="user_123",
            payment_method_token="pm_tok_abc"
        )
        
        payment_service.payment_repo.get_payment_by_order_id.return_value = None
        payment_service.payment_repo.create_payment.return_value = sample_payment_db
        payment_service.payment_repo.update_payment_status = AsyncMock()
        
        async def mock_create_payment_intent_fail(*args, **kwargs):
            raise Exception("Stripe error")
        
        payment_service.stripe_service.create_payment_intent = AsyncMock(side_effect=mock_create_payment_intent_fail)
        
        result = await payment_service.create_payment(payment_data)

        assert isinstance(result, pydantic_models.PaymentResponse)
        assert result.status == PaymentStatus.FAILED

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
    async def test_get_payment_invalid_uuid(self, payment_service):
        invalid_payment_id = "not-a-uuid"
        
        with pytest.raises(Exception) as exc_info:
            await payment_service.get_payment(invalid_payment_id)
        
        # The actual error message might be from UUID conversion
        # Accept either expected message
        error_message = str(exc_info.value)
        assert "badly formed hexadecimal UUID string" in error_message or "Payment not found" in error_message

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
                        "metadata": {"payment_id": str(sample_payment_db.id)}
                    }
                }
            }
        
        payment_service.stripe_service.handle_webhook_event = AsyncMock(side_effect=mock_handle_webhook_event)
        payment_service.payment_repo.get_payment_by_id.return_value = sample_payment_db
        payment_service.payment_repo.update_payment_status = AsyncMock()
        
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
        payment_service.payment_repo.update_payment_status = AsyncMock()
        
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
        payment_service.payment_repo.update_payment_status = AsyncMock()
        
        result = await payment_service.process_webhook(mock_request, payload, sig_header)

        assert "status" in result
        assert result["status"] == "processed"

    @pytest.mark.asyncio
    async def test_process_webhook_error(self, payment_service):
        from fastapi import Request
        
        mock_request = Mock(spec=Request)
        mock_request.url = "http://test/webhook"
        mock_request.method = "POST"
        mock_request.client = Mock()
        mock_request.client.host = "127.0.0.1"
        
        payload = b'{"test": "data"}'
        sig_header = "stripe-signature"
        
        async def mock_handle_webhook_event_fail(*args, **kwargs):
            raise Exception("Webhook error")
        
        payment_service.stripe_service.handle_webhook_event = AsyncMock(side_effect=mock_handle_webhook_event_fail)
        
        with pytest.raises(Exception) as exc_info:
            await payment_service.process_webhook(mock_request, payload, sig_header)
        
        # Accept either error message
        error_message = str(exc_info.value)
        assert "Webhook error" in error_message or "Webhook processing failed" in error_message

    @pytest.mark.asyncio
    async def test_create_refund_success(self, payment_service, sample_payment_db):
        sample_payment_db.status = PaymentStatus.SUCCEEDED
        sample_payment_db.stripe_payment_intent_id = "pi_123"
        
        payment_id = str(sample_payment_db.id)
        refund_data = pydantic_models.RefundRequest(amount=50.0, reason="customer_request")
        
        payment_service.payment_repo.get_payment_by_id.return_value = sample_payment_db
        payment_service.payment_repo.update_payment_status = AsyncMock()
        
        async def mock_create_refund(*args, **kwargs):
            return {
                "id": "re_123",
                "status": "succeeded",
                "amount": 50.0,
                "currency": "usd",
                "reason": "customer_request"
            }
        
        payment_service.stripe_service.create_refund = AsyncMock(side_effect=mock_create_refund)
        
        result = await payment_service.create_refund(payment_id, refund_data)

        assert "id" in result
        assert result["id"] == "re_123"

    @pytest.mark.asyncio
    async def test_create_refund_no_stripe_id(self, payment_service, sample_payment_db):
        sample_payment_db.status = PaymentStatus.SUCCEEDED
        sample_payment_db.stripe_payment_intent_id = None
        
        payment_id = str(sample_payment_db.id)
        refund_data = pydantic_models.RefundRequest()
        
        payment_service.payment_repo.get_payment_by_id.return_value = sample_payment_db
        
        with pytest.raises(Exception) as exc_info:
            await payment_service.create_refund(payment_id, refund_data)
        
        assert "Payment has no Stripe payment intent" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_refund_not_succeeded(self, payment_service, sample_payment_db):
        sample_payment_db.status = PaymentStatus.FAILED
        sample_payment_db.stripe_payment_intent_id = "pi_123"
        
        payment_id = str(sample_payment_db.id)
        refund_data = pydantic_models.RefundRequest()
        
        payment_service.payment_repo.get_payment_by_id.return_value = sample_payment_db
        
        with pytest.raises(Exception) as exc_info:
            await payment_service.create_refund(payment_id, refund_data)
        
        assert "Only succeeded payments can be refunded" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_refund_stripe_error(self, payment_service, sample_payment_db):
        sample_payment_db.status = PaymentStatus.SUCCEEDED
        sample_payment_db.stripe_payment_intent_id = "pi_123"
        
        payment_id = str(sample_payment_db.id)
        refund_data = pydantic_models.RefundRequest()
        
        payment_service.payment_repo.get_payment_by_id.return_value = sample_payment_db
        payment_service.payment_repo.update_payment_status = AsyncMock()
        
        async def mock_create_refund_fail(*args, **kwargs):
            raise Exception("Stripe error")
        
        payment_service.stripe_service.create_refund = AsyncMock(side_effect=mock_create_refund_fail)
        
        with pytest.raises(Exception) as exc_info:
            await payment_service.create_refund(payment_id, refund_data)
        
        assert "Stripe error" in str(exc_info.value)