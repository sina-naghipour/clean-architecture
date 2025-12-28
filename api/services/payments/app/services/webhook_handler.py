from uuid import UUID
from typing import Optional, Tuple
from database.database_models import PaymentDB, PaymentStatus
from repositories.payments_repository import PaymentRepository
from opentelemetry import trace


class WebhookHandler:
    def __init__(self, payment_repo: PaymentRepository, tracer: trace.Tracer):
        self.payment_repo = payment_repo
        self.tracer = tracer
    
    async def handle_stripe_event(self, event_type: str, event_data: dict, payment_id: UUID) -> Tuple[Optional[str], Optional[str]]:
        with self.tracer.start_as_current_span("handle_stripe_event") as span:
            span.set_attributes({
                "stripe.event_type": event_type,
                "payment.id": str(payment_id)
            })
            
            payment = await self.payment_repo.get_payment_by_id(payment_id)
            if not payment:
                return None, None
            
            result = None
            receipt_url = None
            
            if event_type.startswith("payment_intent."):
                result = await self._handle_payment_intent(event_type, event_data, payment)
            elif event_type.startswith("charge."):
                result = await self._handle_charge(event_type, event_data, payment)
                if result == "succeeded":
                    receipt_url = event_data.get("receipt_url")
            
            if result:
                span.set_attribute("payment.new_status", result.upper())
            
            return result, receipt_url
    
    async def _handle_payment_intent(self, event_type: str, event_data: dict, payment: PaymentDB) -> Optional[str]:
        if event_type == "payment_intent.payment_failed":
            await self.payment_repo.update_payment_status(payment.id, PaymentStatus.FAILED)
            return "failed"
        elif event_type == "payment_intent.created":
            await self.payment_repo.update_payment_status(payment.id, PaymentStatus.CREATED)
            if event_data.get("client_secret"):
                await self.payment_repo.update_payment_client_secret(payment.id, event_data.get("client_secret"))
            return "created"
        elif event_type == "payment_intent.canceled":
            await self.payment_repo.update_payment_status(payment.id, PaymentStatus.CANCELED)
            return "canceled"
        return None
    
    async def _handle_charge(self, event_type: str, event_data: dict, payment: PaymentDB) -> Optional[str]:
        if event_type == "charge.refunded":
            await self.payment_repo.update_payment_status(payment.id, PaymentStatus.REFUNDED)
            return "refunded"
        elif event_type == "charge.succeeded" and event_data.get("status") == "succeeded":
            await self.payment_repo.update_payment_status(payment.id, PaymentStatus.SUCCEEDED)
            return "succeeded"
        return None