import os
import logging
import stripe
from typing import Dict, Any, Optional
from database.database_models import PaymentStatus
from optl.trace_decorator import trace_service_operation
from opentelemetry import trace
from dotenv import load_dotenv

load_dotenv()
class StripeService:
    def __init__(self, logger: logging.Logger = None):
        self.logger = logger or logging.getLogger(__name__).getChild("StripeService")
        self.stripe_mode = os.getenv("STRIPE_MODE", "test")
        self.secret_key = os.getenv("STRIPE_SECRET_KEY", "sk_test")
        self.tracer = trace.get_tracer(__name__)

        stripe.api_key = self.secret_key
        
        api_base = os.getenv("STRIPE_API_BASE")
        if api_base:
            stripe.api_base = api_base
            self.logger.info(f"Stripe service initialized with custom API base: {api_base}")
        else:
            self.logger.info(f"Stripe service initialized in {self.stripe_mode} mode")
        
        self.webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "whsec_mock")
    
    @trace_service_operation("create_payment_intent")
    async def create_payment_intent(
        self,
        amount: float,
        currency: str,
        payment_method_token: str,
        metadata: Dict[str, Any] = None,
        customer_id: Optional[str] = None
    ) -> Dict[str, Any]:
        try:
            with self.tracer.start_as_current_span("stripe.create_payment_intent") as span:
                span.set_attributes({
                    "stripe.operation": "create_payment_intent",
                    "stripe.amount": amount,
                    "stripe.currency": currency,
                    "stripe.mode": self.stripe_mode,
                    "customer.id": customer_id or "none"
                })
                
                self.logger.info(f"Creating payment intent for amount: {amount} {currency}")
                
                intent_data = {
                    "amount": int(amount * 100),
                    "currency": currency,
                    "payment_method": payment_method_token,
                    "confirm": False,
                    "metadata": metadata or {},
                    "payment_method_types": ["card"]
                }
                
                if customer_id:
                    intent_data["customer"] = customer_id
                
                payment_intent = stripe.PaymentIntent.create(**intent_data)
                
                self.logger.info(f"Payment intent created: {payment_intent.id}")
                span.set_attributes({
                    "stripe.payment_intent.id": payment_intent.id,
                    "stripe.payment_intent.status": payment_intent.status
                })
                
                return {
                    "id": payment_intent.id,
                    "status": payment_intent.status,
                    "amount": payment_intent.amount / 100,
                    "client_secret": payment_intent.client_secret
                }
                
        except stripe.error.StripeError as e:
            span = trace.get_current_span()
            span.record_exception(e)
            span.set_attribute("stripe.error", True)
            span.set_attribute("stripe.error_type", type(e).__name__)
            self.logger.error(f"Stripe error creating payment intent: {e}")
            raise Exception(f"Stripe payment failed: {e.user_message if hasattr(e, 'user_message') else str(e)}")
        except Exception as e:
            span = trace.get_current_span()
            span.record_exception(e)
            self.logger.error(f"Unexpected error creating payment intent: {e}")
            raise
    
    @trace_service_operation("retrieve_payment_intent")
    async def retrieve_payment_intent(self, payment_intent_id: str) -> Dict[str, Any]:
        try:
            with self.tracer.start_as_current_span("stripe.retrieve_payment_intent") as span:
                span.set_attributes({
                    "stripe.operation": "retrieve_payment_intent",
                    "stripe.payment_intent.id": payment_intent_id
                })
                
                self.logger.info(f"Retrieving payment intent: {payment_intent_id}")
                
                payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
                
                span.set_attribute("stripe.payment_intent.status", payment_intent.status)
                
                return {
                    "id": payment_intent.id,
                    "status": payment_intent.status,
                    "amount": payment_intent.amount / 100,
                    "currency": payment_intent.currency,
                    "client_secret": payment_intent.client_secret,
                    "metadata": payment_intent.metadata
                }
                
        except stripe.error.StripeError as e:
            span = trace.get_current_span()
            span.record_exception(e)
            span.set_attribute("stripe.error", True)
            self.logger.error(f"Stripe error retrieving payment intent: {e}")
            raise
        except Exception as e:
            span = trace.get_current_span()
            span.record_exception(e)
            self.logger.error(f"Unexpected error retrieving payment intent: {e}")
            raise
    
    @trace_service_operation("create_refund")
    async def create_refund(
        self,
        payment_intent_id: str,
        amount: Optional[float] = None,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        try:
            with self.tracer.start_as_current_span("stripe.create_refund") as span:
                span.set_attributes({
                    "stripe.operation": "create_refund",
                    "stripe.payment_intent.id": payment_intent_id,
                    "stripe.refund.amount": amount if amount else "full",
                    "stripe.refund.reason": reason or "unknown"
                })
                
                self.logger.info(f"Creating refund for payment intent: {payment_intent_id}")
                
                refund_data = {"payment_intent": payment_intent_id}
                
                if amount:
                    refund_data["amount"] = int(amount * 100)
                
                if reason:
                    refund_data["reason"] = reason
                
                refund = stripe.Refund.create(**refund_data)
                
                self.logger.info(f"Refund created: {refund.id}")
                span.set_attribute("stripe.refund.id", refund.id)
                span.set_attribute("stripe.refund.status", refund.status)
                
                return {
                    "id": refund.id,
                    "status": refund.status,
                    "amount": refund.amount / 100,
                    "currency": refund.currency,
                    "reason": refund.reason
                }
                
        except stripe.error.StripeError as e:
            span = trace.get_current_span()
            span.record_exception(e)
            span.set_attribute("stripe.error", True)
            self.logger.error(f"Stripe error creating refund: {e}")
            raise Exception(f"Refund failed: {e.user_message if hasattr(e, 'user_message') else str(e)}")
        except Exception as e:
            span = trace.get_current_span()
            span.record_exception(e)
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
        
    @trace_service_operation("handle_webhook_event")
    async def handle_webhook_event(self, payload: bytes, sig_header: str) -> Dict[str, Any]:
        try:
            with self.tracer.start_as_current_span("stripe.handle_webhook") as span:
                import json
                
                if not sig_header and os.getenv("ENVIRONMENT") == "production":
                    self.logger.error("Missing Stripe signature header in production")
                    span.set_attribute("stripe.missing_signature", True)
                    raise ValueError("Missing Stripe-Signature header")
                
                try:
                    payload_str = payload.decode('utf-8')
                    payload_dict = json.loads(payload_str)
                except (UnicodeDecodeError, json.JSONDecodeError) as e:
                    self.logger.warning(f"Failed to parse webhook payload: {e}")
                    span.set_attribute("stripe.payload_parse_error", str(e))
                    return {
                        "type": "unknown",
                        "id": "mock_event_id",
                        "data": {"object": {}},
                        "created": 1234567890
                    }
                
                event_type = payload_dict.get('type')
                event_id = payload_dict.get('id')
                created = payload_dict.get('created')
                data_object = payload_dict.get('data', {}).get('object', {})
                
                self.logger.info(f"Parsed Stripe webhook event: {event_type}")
                span.set_attributes({
                    "stripe.event_type": event_type,
                    "stripe.event_id": event_id or "mock",
                    "stripe.signature_present": bool(sig_header)
                })
                

                if self.webhook_secret and self.webhook_secret != "whsec_mock":
                    try:
                        event = stripe.Webhook.construct_event(payload, sig_header, self.webhook_secret)
                        self.logger.info(f"Successfully verified Stripe webhook signature for event: {event_type}")
                        span.set_attribute("stripe.signature_verified", True)
                        
                        return {
                            "type": event.type,
                            "id": event.id,
                            "data": {"object": event.data.object},
                            "created": event.created
                        }
                    except stripe.error.SignatureVerificationError as sig_error:
                        self.logger.error(f"Stripe signature verification failed: {sig_error}")
                        span.set_attribute("stripe.signature_verified", False)
                        span.set_attribute("stripe.signature_error", str(sig_error))
                        
                        if os.getenv("ENVIRONMENT") == "production":
                            raise ValueError(f"Invalid webhook signature: {sig_error}")
                else:
                    self.logger.warning(f"Webhook secret not configured or using mock secret, skipping verification for event: {event_type}")
                    span.set_attribute("stripe.signature_verified", "skipped")
                
                event_dict = {
                    "type": event_type,
                    "id": event_id if event_id else "mock_event_id",
                    "data": {
                        "object": data_object
                    },
                    "created": created if created else 1234567890
                }
                
                if os.getenv("ENVIRONMENT") == "production" and not (self.webhook_secret and self.webhook_secret != "whsec_mock"):
                    self.logger.warning(f"Processing unverified webhook in production: {event_type}")
                
                return event_dict
                
        except Exception as e:
            span = trace.get_current_span()
            span.record_exception(e)
            span.set_attribute("stripe.error", True)
            span.set_attribute("stripe.error_type", type(e).__name__)
            self.logger.error(f"Error handling webhook event: {e}")
            return {
                "type": "unknown",
                "id": "mock_event_id",
                "data": {"object": {}},
                "created": 1234567890
            }
    async def create_checkout_session(self, amount, currency, order_id, user_id, success_url, cancel_url, metadata=None):
        try:
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': currency,
                        'product_data': {'name': f'Order #{order_id}'},
                        'unit_amount': int(amount * 100),
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={
                    'order_id': order_id,
                    'user_id': user_id,
                    'payment_type': 'checkout_session',
                    **(metadata or {})
                }
            )
            return {
                'id': session.id,
                'url': session.url,
                'payment_intent_id': session.payment_intent,
                'type': 'checkout',
                'client_secret' : 'NONE'
            }
        except stripe.error.StripeError as e:
            self.logger.error(f"Stripe Checkout failed: {e}")
            raise Exception(f"Checkout creation failed: {e.user_message}")

    async def create_payment(self, amount, currency, payment_method_token, metadata, checkout_mode=True, success_url=None, cancel_url=None):
        with self.tracer.start_as_current_span("stripe.create_payment") as span:
            span.set_attributes({
                "stripe.amount": amount,
                "stripe.currency": currency,
                "stripe.mode": self.stripe_mode,
                "stripe.checkout_mode": checkout_mode
            })
            
            if checkout_mode:
                if not success_url or not cancel_url:
                    raise Exception("Checkout mode requires success_url and cancel_url")
                
                result = await self.create_checkout_session(
                    amount=amount,
                    currency=currency,
                    order_id=metadata.get('order_id'),
                    user_id=metadata.get('user_id'),
                    success_url=success_url,
                    cancel_url=cancel_url,
                    metadata=metadata
                )
                span.set_attribute("stripe.payment_type", "checkout_session")
                span.set_attribute("stripe.checkout_url", result.get('url', ''))
                
                return result
            else:
                result = await self.create_payment_intent(
                    amount=amount,
                    currency=currency,
                    payment_method_token=payment_method_token,
                    metadata=metadata
                )
                span.set_attribute("stripe.payment_type", "payment_intent")
                return result

    async def retrieve_checkout_session(self, session_id):
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            
            return {
                'id': session.id,
                'status': session.status,
                'payment_intent_id': session.payment_intent,
                'amount_total': session.amount_total / 100,
                'currency': session.currency,
                'metadata': session.metadata
            }
        except stripe.error.StripeError as e:
            self.logger.error(f"Failed to retrieve checkout session: {e}")
            raise



