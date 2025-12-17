import pytest
from unittest.mock import Mock, patch
from services.stripe_service import StripeService
from database.database_models import PaymentStatus

class TestStripeService:
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