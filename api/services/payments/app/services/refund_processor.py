from uuid import UUID
from database import pydantic_models
from database.database_models import PaymentStatus
from repositories.payments_repository import PaymentRepository
from .stripe_service import StripeService
import logging

class RefundProcessor:
    def __init__(self, payment_repo: PaymentRepository, stripe_service: StripeService, logger: logging.Logger):
        self.payment_repo = payment_repo
        self.stripe_service = stripe_service
        self.logger = logger
    
    async def process_refund(self, payment_id: str, refund_data: pydantic_models.RefundRequest) -> dict:
        payment_uuid = UUID(payment_id)
        payment = await self.payment_repo.get_payment_by_id(payment_uuid)
        
        if not payment:
            raise Exception(f"Payment not found: {payment_id}")
        
        if not payment.stripe_payment_intent_id:
            raise Exception("Payment has no Stripe payment intent")
        
        if payment.status != PaymentStatus.SUCCEEDED:
            raise Exception("Only succeeded payments can be refunded")
        
        refund_result = await self.stripe_service.create_refund(
            payment_intent_id=payment.stripe_payment_intent_id,
            amount=refund_data.amount,
            reason=refund_data.reason
        )
        
        await self.payment_repo.update_payment_status(payment.id, PaymentStatus.REFUNDED)
        
        return {
            "id": refund_result["id"],
            "status": refund_result["status"],
            "amount": refund_result["amount"],
            "currency": refund_result["currency"],
            "reason": refund_result["reason"]
        }