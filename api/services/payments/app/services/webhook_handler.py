from uuid import UUID
from typing import Optional, Tuple
from database.database_models import PaymentDB, PaymentStatus
from repositories.payments_repository import PaymentRepository
from opentelemetry import trace
import logging

class WebhookHandler:
    def __init__(self, payment_repo: PaymentRepository, tracer: trace.Tracer, logger: logging.Logger, referral_service=None):
        self.payment_repo = payment_repo
        self.tracer = tracer
        self.logger = logger
        self.referral_service = referral_service
    
    async def handle_stripe_event(self, event_type: str, event_data: dict, payment_id: UUID) -> Tuple[Optional[str], Optional[str]]:
        with self.tracer.start_as_current_span("handle_stripe_event") as span:
            span.set_attributes({
                "stripe.event_type": event_type,
                "payment.id": str(payment_id)
            })
            
            payment = await self.payment_repo.get_payment_by_id(payment_id)
            if not payment:
                self.logger.warning(f"Payment not found: {payment_id}")
                return None, None
            
            result = None
            receipt_url = None
            
            self.logger.info(f"Handling {event_type} for payment {payment_id}, current status: {payment.status}")
            
            if event_type.startswith("checkout.session"):
                result = await self._handle_checkout_session(event_type, event_data, payment)
            elif event_type.startswith("payment_intent."):
                result = await self._handle_payment_intent(event_type, event_data, payment)
            elif event_type.startswith("charge."):
                result = await self._handle_charge(event_type, event_data, payment)
                if result == "succeeded":
                    receipt_url = event_data.get("receipt_url")
            
            if result == "succeeded" and payment.referral_code and self.referral_service:
                try:
                    await self.referral_service.accrue_commission(
                        order_id=payment.order_id,
                        customer_id=payment.user_id,
                        amount=payment.amount,
                        referral_code=payment.referral_code
                    )
                    span.set_attribute("referral.commission_attempted", True)
                    self.logger.info(f"Referral commission attempted for order: {payment.order_id}")
                except Exception as e:
                    self.logger.error(f"Failed to accrue referral commission: {e}", exc_info=True)
                    span.set_attribute("referral.error", str(e))
            
            if result:
                span.set_attribute("payment.new_status", result.upper())
                self.logger.info(f"Payment {payment_id} updated to {result}")
            else:
                self.logger.info(f"No status change for {event_type}")
            
            return result, receipt_url
    
    async def _handle_checkout_session(self, event_type: str, event_data: dict, payment: PaymentDB) -> Optional[str]:
        if event_type == "checkout.session.completed":
            session = event_data
            payment_intent_id = session.get("payment_intent")
            
            if payment_intent_id:
                await self.payment_repo.update_payment_stripe_id(payment.id, payment_intent_id)
            
            await self.payment_repo.update_payment_status(payment.id, PaymentStatus.SUCCEEDED)
            return "succeeded"
        
        elif event_type == "checkout.session.expired":
            await self.payment_repo.update_payment_status(payment.id, PaymentStatus.CANCELED)
            return "canceled"
        
        elif event_type == "checkout.session.async_payment_failed":
            await self.payment_repo.update_payment_status(payment.id, PaymentStatus.FAILED)
            return "failed"
        
        return None
    
    async def _handle_payment_intent(self, event_type: str, event_data: dict, payment: PaymentDB) -> Optional[str]:
        if event_type == "payment_intent.payment_failed":
            await self.payment_repo.update_payment_status(payment.id, PaymentStatus.FAILED)
            return "failed"
        elif event_type == "payment_intent.created":
            if payment.status in [PaymentStatus.CREATED, PaymentStatus.PENDING]:
                await self.payment_repo.update_payment_status(payment.id, PaymentStatus.CREATED)
                if event_data.get("client_secret"):
                    await self.payment_repo.update_payment_client_secret(payment.id, event_data.get("client_secret"))
                return "created"
            else:
                self.logger.info(f"Ignoring payment_intent.created for payment {payment.id} - already {payment.status}")
                return None
        elif event_type == "payment_intent.canceled":
            await self.payment_repo.update_payment_status(payment.id, PaymentStatus.CANCELED)
            return "canceled"
        return None
    
    async def _handle_charge(self, event_type: str, event_data: dict, payment: PaymentDB) -> Optional[str]:
        if event_type == "charge.refunded":
            await self.payment_repo.update_payment_status(payment.id, PaymentStatus.REFUNDED)
            return "refunded"
        elif event_type == "charge.succeeded":
            await self.payment_repo.update_payment_status(payment.id, PaymentStatus.SUCCEEDED)
            self.logger.info(f"Charge succeeded for payment ID: {payment.id}")
            return "succeeded"
        elif event_type == "charge.updated":
            if event_data.get("status") == "succeeded" and event_data.get("paid") == True:
                await self.payment_repo.update_payment_status(payment.id, PaymentStatus.SUCCEEDED)
                self.logger.info(f"Charge updated to succeeded for payment ID: {payment.id}")
                return "succeeded"
        return None