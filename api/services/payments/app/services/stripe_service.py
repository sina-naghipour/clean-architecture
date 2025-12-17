import os
import logging
import stripe
from typing import Dict, Any, Optional
from database.database_models import PaymentStatus

class StripeService:
    def __init__(self, logger: logging.Logger = None):
        self.logger = logger or logging.getLogger(__name__).getChild("StripeService")
        self.stripe_mode = os.getenv("STRIPE_MODE", "test")
        self.secret_key = os.getenv("STRIPE_SECRET_KEY", "sk_test_mock")
        
        stripe.api_key = self.secret_key
        
        api_base = os.getenv("STRIPE_API_BASE")
        if api_base:
            stripe.api_base = api_base
            self.logger.info(f"Stripe service initialized with custom API base: {api_base}")
        else:
            self.logger.info(f"Stripe service initialized in {self.stripe_mode} mode")
        
        self.webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "whsec_mock")
    
    async def create_payment_intent(
        self,
        amount: float,
        currency: str,
        payment_method_token: str,
        metadata: Dict[str, Any] = None,
        customer_id: Optional[str] = None
    ) -> Dict[str, Any]:
        try:
            self.logger.info(f"Creating payment intent for amount: {amount} {currency}")
            
            intent_data = {
                "amount": int(amount * 100),
                "currency": currency,
                "payment_method": payment_method_token,
                "confirm": True,
                "metadata": metadata or {}
            }
            
            if customer_id:
                intent_data["customer"] = customer_id
            
            payment_intent = stripe.PaymentIntent.create(**intent_data)
            
            self.logger.info(f"Payment intent created: {payment_intent.id}")
            return {
                "id": payment_intent.id,
                "status": payment_intent.status,
                "amount": payment_intent.amount / 100
            }
            
        except stripe.error.StripeError as e:
            self.logger.error(f"Stripe error creating payment intent: {e}")
            raise Exception(f"Stripe payment failed: {e.user_message if hasattr(e, 'user_message') else str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error creating payment intent: {e}")
            raise
    
    async def retrieve_payment_intent(self, payment_intent_id: str) -> Dict[str, Any]:
        try:
            self.logger.info(f"Retrieving payment intent: {payment_intent_id}")
            
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            
            return {
                "id": payment_intent.id,
                "status": payment_intent.status,
                "amount": payment_intent.amount / 100,
                "currency": payment_intent.currency,
                "metadata": payment_intent.metadata
            }
            
        except stripe.error.StripeError as e:
            self.logger.error(f"Stripe error retrieving payment intent: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error retrieving payment intent: {e}")
            raise
    
    async def create_refund(
        self,
        payment_intent_id: str,
        amount: Optional[float] = None,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        try:
            self.logger.info(f"Creating refund for payment intent: {payment_intent_id}")
            
            refund_data = {"payment_intent": payment_intent_id}
            
            if amount:
                refund_data["amount"] = int(amount * 100)
            
            if reason:
                refund_data["reason"] = reason
            
            refund = stripe.Refund.create(**refund_data)
            
            self.logger.info(f"Refund created: {refund.id}")
            return {
                "id": refund.id,
                "status": refund.status,
                "amount": refund.amount / 100,
                "currency": refund.currency,
                "reason": refund.reason
            }
            
        except stripe.error.StripeError as e:
            self.logger.error(f"Stripe error creating refund: {e}")
            raise Exception(f"Refund failed: {e.user_message if hasattr(e, 'user_message') else str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error creating refund: {e}")
            raise
    
    def map_stripe_status_to_payment_status(self, stripe_status: str) -> PaymentStatus:
        status_mapping = {
            "requires_payment_method": PaymentStatus.CREATED,
            "requires_confirmation": PaymentStatus.PROCESSING,
            "requires_action": PaymentStatus.PROCESSING,
            "processing": PaymentStatus.PROCESSING,
            "requires_capture": PaymentStatus.PROCESSING,
            "canceled": PaymentStatus.CANCELED,
            "succeeded": PaymentStatus.SUCCEEDED
        }
        
        return status_mapping.get(stripe_status, PaymentStatus.FAILED)
    
    async def handle_webhook_event(self, payload: bytes, sig_header: str) -> Dict[str, Any]:
        try:
            if not self.webhook_secret:
                self.logger.error("STRIPE_WEBHOOK_SECRET not configured")
                raise ValueError("Webhook secret not configured")
            
            if os.getenv("STRIPE_API_BASE"):
                event = stripe.Webhook.construct_event(payload, sig_header, self.webhook_secret)
            else:
                import json
                event_data = json.loads(payload)
                event = type('Event', (), {
                    'type': event_data.get('type'),
                    'id': event_data.get('id'),
                    'data': type('Data', (), {'object': event_data.get('data', {}).get('object', {})})(),
                    'created': event_data.get('created')
                })()
            
            self.logger.info(f"Received Stripe webhook event: {event.type}")
            
            event_dict = {
                "type": event.type,
                "id": event.id if hasattr(event, 'id') else "mock_event_id",
                "data": event.data.__dict__ if hasattr(event.data, '__dict__') else event.data,
                "created": event.created if hasattr(event, 'created') else 1234567890
            }
            
            return event_dict
            
        except Exception as e:
            self.logger.error(f"Error handling webhook event: {e}")
            raise Exception(f"Webhook processing failed: {str(e)}")