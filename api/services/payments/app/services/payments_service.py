from .stripe_service import StripeService
from database import pydantic_models
from uuid import UUID
from repositories.payments_repository import PaymentRepository
from database.database_models import PaymentDB, PaymentStatus
import logging

class PaymentService:
    def __init__(self, logger: logging.Logger, db_session):
        self.logger = logger
        self.payment_repo = PaymentRepository(db_session)
        self.stripe_service = StripeService(logger)
    
    async def create_payment(self, payment_data: pydantic_models.PaymentCreate):
        existing_payment = await self.payment_repo.get_payment_by_order_id(payment_data.order_id)
        if existing_payment:
            raise Exception(f"Payment already exists for order: {payment_data.order_id}")
        
        payment = PaymentDB(
            order_id=payment_data.order_id,
            user_id=payment_data.user_id,
            amount=payment_data.amount,
            payment_method_token=payment_data.payment_method_token,
            currency=payment_data.currency,
            payment_metadata=payment_data.metadata,
            status=PaymentStatus.CREATED
        )
        
        created_payment = await self.payment_repo.create_payment(payment)
        
        try:
            stripe_result = await self.stripe_service.create_payment_intent(
                amount=payment_data.amount,
                currency=payment_data.currency,
                payment_method_token=payment_data.payment_method_token,
                metadata={
                    "order_id": payment_data.order_id,
                    "user_id": payment_data.user_id,
                    "payment_id": str(created_payment.id)
                }
            )
            
            await self.payment_repo.update_payment_stripe_id(created_payment.id, stripe_result["id"])
            
            payment_status = self.stripe_service.map_stripe_status_to_payment_status(stripe_result["status"])
            await self.payment_repo.update_payment_status(created_payment.id, payment_status)
            
            created_payment.stripe_payment_intent_id = stripe_result["id"]
            created_payment.status = payment_status
            
        except Exception:
            await self.payment_repo.update_payment_status(created_payment.id, PaymentStatus.FAILED)
            created_payment.status = PaymentStatus.FAILED
        
        return pydantic_models.PaymentResponse(
            id=str(created_payment.id),
            order_id=created_payment.order_id,
            user_id=created_payment.user_id,
            amount=created_payment.amount,
            status=created_payment.status,
            stripe_payment_intent_id=created_payment.stripe_payment_intent_id,
            payment_method_token=created_payment.payment_method_token,
            currency=created_payment.currency,
            metadata=created_payment.payment_metadata,
            created_at=created_payment.created_at.isoformat(),
            updated_at=created_payment.updated_at.isoformat()
        )
    
    async def get_payment(self, payment_id: str):
        payment_uuid = UUID(payment_id)
        payment = await self.payment_repo.get_payment_by_id(payment_uuid)
        
        if not payment:
            raise Exception(f"Payment not found: {payment_id}")
        
        return pydantic_models.PaymentResponse(
            id=str(payment.id),
            order_id=payment.order_id,
            user_id=payment.user_id,
            amount=payment.amount,
            status=payment.status,
            stripe_payment_intent_id=payment.stripe_payment_intent_id,
            payment_method_token=payment.payment_method_token,
            currency=payment.currency,
            metadata=payment.payment_metadata,
            created_at=payment.created_at.isoformat(),
            updated_at=payment.updated_at.isoformat()
        )
    
    async def process_webhook(self, payload: bytes, sig_header: str):
        event = await self.stripe_service.handle_webhook_event(payload, sig_header)
        event_type = event["type"]
        
        payment_intent = event["data"]
        if isinstance(payment_intent, dict) and "object" in payment_intent:
            payment_intent = payment_intent["object"]
        payment_intent_id = payment_intent.get("id")
        
        if event_type == "payment_intent.succeeded" and payment_intent_id:
            payment = await self.payment_repo.get_payment_by_stripe_id(payment_intent_id)
            if payment:
                await self.payment_repo.update_payment_status(payment.id, PaymentStatus.SUCCEEDED)
        
        elif event_type == "payment_intent.payment_failed" and payment_intent_id:
            payment = await self.payment_repo.get_payment_by_stripe_id(payment_intent_id)
            if payment:
                await self.payment_repo.update_payment_status(payment.id, PaymentStatus.FAILED)
        
        return {"status": "processed", "event": event_type}
    
    async def create_refund(self, payment_id: str, refund_data: pydantic_models.RefundRequest):
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