import pytest
from unittest.mock import Mock, patch
from services.stripe_service import StripeService
from database.database_models import PaymentStatus

class TestStripeService:
    @pytest.fixture
    def mock_stripe(self):
        with patch('stripe.checkout.Session') as mock_session, \
             patch('stripe.PaymentIntent') as mock_intent, \
             patch('stripe.Refund') as mock_refund, \
             patch('stripe.Webhook') as mock_webhook:
            yield {
                'checkout.Session': mock_session,
                'PaymentIntent': mock_intent,
                'Refund': mock_refund,
                'Webhook': mock_webhook
            }
    
    @pytest.fixture
    def stripe_service(self):
        with patch.dict('os.environ', {
            'STRIPE_SECRET_KEY': 'sk_test_mock',
            'STRIPE_WEBHOOK_SECRET': 'whsec_mock'
        }):
            service = StripeService()
            return service
    
    def test_map_stripe_status_to_payment_status(self, stripe_service):
        assert stripe_service.map_stripe_status_to_payment_status("requires_payment_method") == PaymentStatus.CREATED
        assert stripe_service.map_stripe_status_to_payment_status("requires_confirmation") == PaymentStatus.PROCESSING
        assert stripe_service.map_stripe_status_to_payment_status("processing") == PaymentStatus.PROCESSING
        assert stripe_service.map_stripe_status_to_payment_status("succeeded") == PaymentStatus.SUCCEEDED
        assert stripe_service.map_stripe_status_to_payment_status("canceled") == PaymentStatus.CANCELED
        assert stripe_service.map_stripe_status_to_payment_status("unknown") == PaymentStatus.FAILED

    @pytest.mark.asyncio
    async def test_create_checkout_session_mode(self, stripe_service, mock_stripe):
        mock_session = Mock()
        mock_session.id = 'cs_test_123'
        mock_session.url = 'https://checkout.stripe.com/c/pay/cs_test_123'
        mock_session.payment_intent = 'pi_123'
        mock_session.status = 'open'
        mock_stripe['checkout.Session'].create.return_value = mock_session
        
        result = await stripe_service.create_checkout_session(
            amount=100.0,
            currency='usd',
            order_id='order_123',
            user_id='user_123',
            success_url='https://example.com/success',
            cancel_url='https://example.com/cancel',
            metadata={'test': 'data'}
        )
        
        assert result['type'] == 'checkout'
        assert result['url'] == 'https://checkout.stripe.com/c/pay/cs_test_123'
        assert result['payment_intent_id'] == 'pi_123'

    @pytest.mark.asyncio
    async def test_create_payment_checkout_mode(self, stripe_service, mock_stripe):
        mock_session = Mock()
        mock_session.id = 'cs_test_456'
        mock_session.url = 'https://checkout.stripe.com/c/pay/cs_test_456'
        mock_session.payment_intent = 'pi_456'
        mock_session.status = 'open'
        mock_stripe['checkout.Session'].create.return_value = mock_session
        
        result = await stripe_service.create_payment(
            amount=200.0,
            currency='usd',
            payment_method_token='pm_123',
            metadata={'order_id': 'order_456', 'user_id': 'user_456'},
            checkout_mode=True,
            success_url='https://example.com/success',
            cancel_url='https://example.com/cancel'
        )
        
        assert result['type'] == 'checkout'
        assert 'checkout.stripe.com' in result['url']

    @pytest.mark.asyncio
    async def test_create_payment_intent_mode(self, stripe_service, mock_stripe):
        mock_intent = Mock()
        mock_intent.id = 'pi_789'
        mock_intent.client_secret = 'pi_789_secret'
        mock_intent.status = 'requires_payment_method'
        mock_intent.amount = 30000  # 300.00 * 100
        mock_intent.currency = 'usd'
        mock_intent.metadata = {'order_id': 'order_789'}
        mock_stripe['PaymentIntent'].create.return_value = mock_intent
        
        result = await stripe_service.create_payment(
            amount=300.0,
            currency='usd',
            payment_method_token='pm_789',
            metadata={'order_id': 'order_789'},
            checkout_mode=False
        )
        
        assert 'client_secret' in result
        assert result['id'] == 'pi_789'
        assert result['amount'] == 300.0

    def test_map_checkout_status_to_payment_status_should_not_exist(self, stripe_service):
        pass