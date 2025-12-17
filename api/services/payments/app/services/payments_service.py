from .payments_helpers import create_problem_response
from .stripe_service import StripeService
from fastapi import Request
from fastapi.responses import JSONResponse
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
    
    async def create_payment(
        self,
        request: Request,
        payment_data: pydantic_models.PaymentCreate
    ):
        self.logger.info(f"Payment creation attempt for order: {payment_data.order_id}")
        
        try:
            
            existing_payment = await self.payment_repo.get_payment_by_order_id(payment_data.order_id)
            if existing_payment:
                return create_problem_response(
                    status_code=409,
                    error_type="conflict",
                    title="Conflict",
                    detail="Payment already exists for this order",
                    instance=str(request.url)
                )
            
            payment_db = PaymentDB(
                order_id=payment_data.order_id,
                user_id=payment_data.user_id,
                amount=payment_data.amount,
                payment_method_token=payment_data.payment_method_token,
                currency=payment_data.currency,
                payment_metadata=payment_data.metadata,
                status=PaymentStatus.CREATED
            )
            created_payment = await self.payment_repo.create_payment(payment_db)
            self.logger.info(f"Payment record created: {created_payment.id}")
            
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
                
                
                await self.payment_repo.update_payment_stripe_id(
                    created_payment.id,
                    stripe_result["id"]
                )
                
                payment_status = self.stripe_service.map_stripe_status_to_payment_status(stripe_result["status"])
                await self.payment_repo.update_payment_status(created_payment.id, payment_status)
                
                created_payment.stripe_payment_intent_id = stripe_result["id"]
                created_payment.status = payment_status
                
                self.logger.info(f"Stripe payment intent created: {stripe_result['id']}")

            except Exception as stripe_error:
                self.logger.error(f"Stripe processing failed: {stripe_error}")
                await self.payment_repo.update_payment_status(created_payment.id, PaymentStatus.FAILED)
                created_payment.status = PaymentStatus.FAILED

            payment_response = pydantic_models.PaymentResponse(
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

            return JSONResponse(
                status_code=201,
                content=payment_response.model_dump(),
                headers={"Location": f"/payments/{created_payment.id}"}
            )
            
        except Exception as e:
            self.logger.error(f"Payment creation failed: {e}")
            print('hereeeeeeeeeeeeeeeee: ', e)
            return create_problem_response(
                status_code=500,
                error_type="internal-error",
                title="Internal Server Error",
                detail="Failed to create payment",
                instance=str(request.url)
            )
    
    async def get_payment(
        self,
        request: Request,
        payment_id: str
    ):
        try:
            payment_uuid = UUID(payment_id)
        except ValueError:
            return create_problem_response(
                status_code=400,
                error_type="bad-request",
                title="Bad Request",
                detail="Invalid payment ID format",
                instance=str(request.url)
            )
        
        try:
            payment_db = await self.payment_repo.get_payment_by_id(payment_uuid)
            
            if not payment_db:
                return create_problem_response(
                    status_code=404,
                    error_type="not-found",
                    title="Not Found",
                    detail="Payment not found",
                    instance=str(request.url)
                )
            
            payment_response = pydantic_models.PaymentResponse(
                id=str(payment_db.id),
                order_id=payment_db.order_id,
                user_id=payment_db.user_id,
                amount=payment_db.amount,
                status=payment_db.status,
                stripe_payment_intent_id=payment_db.stripe_payment_intent_id,
                payment_method_token=payment_db.payment_method_token,
                currency=payment_db.currency,
                metadata=payment_db.payment_metadata,
                created_at=payment_db.created_at.isoformat(),
                updated_at=payment_db.updated_at.isoformat()
            )
            
            return payment_response
            
        except Exception as e:
            self.logger.error(f"Payment retrieval failed: {e}")
            return create_problem_response(
                status_code=500,
                error_type="internal-error",
                title="Internal Server Error",
                detail="Failed to retrieve payment",
                instance=str(request.url)
            )
    
    async def process_webhook(
        self,
        request: Request,
        payload: bytes,
        sig_header: str
    ):
        try:
            event_data = await self.stripe_service.handle_webhook_event(payload, sig_header)
            event_type = event_data["type"]
            
            self.logger.info(f"Processing webhook event: {event_type}")
            
            payment_intent = event_data["data"]
            if isinstance(payment_intent, dict) and "object" in payment_intent:
                payment_intent = payment_intent["object"]
            payment_intent_id = payment_intent.get("id")
            
            if event_type == "payment_intent.succeeded" and payment_intent_id:
                payment_db = await self.payment_repo.get_payment_by_stripe_id(payment_intent_id)
                if payment_db:
                    await self.payment_repo.update_payment_status(payment_db.id, PaymentStatus.SUCCEEDED)
                    self.logger.info(f"Payment marked as succeeded: {payment_db.id}")
            
            elif event_type == "payment_intent.payment_failed" and payment_intent_id:
                payment_db = await self.payment_repo.get_payment_by_stripe_id(payment_intent_id)
                if payment_db:
                    await self.payment_repo.update_payment_status(payment_db.id, PaymentStatus.FAILED)
                    self.logger.info(f"Payment marked as failed: {payment_db.id}")
            
            return {"status": "processed", "event": event_type}
            
        except Exception as e:
            self.logger.error(f"Webhook processing failed: {e}")
            return create_problem_response(
                status_code=400,
                error_type="bad-request",
                title="Bad Request",
                detail=str(e),
                instance=str(request.url)
            )
    
    async def create_refund(
        self,
        request: Request,
        payment_id: str,
        refund_data: pydantic_models.RefundRequest
    ):
        try:
            payment_uuid = UUID(payment_id)
        except ValueError:
            return create_problem_response(
                status_code=400,
                error_type="bad-request",
                title="Bad Request",
                detail="Invalid payment ID format",
                instance=str(request.url)
            )
        
        try:
            payment_db = await self.payment_repo.get_payment_by_id(payment_uuid)
            
            if not payment_db:
                return create_problem_response(
                    status_code=404,
                    error_type="not-found",
                    title="Not Found",
                    detail="Payment not found",
                    instance=str(request.url)
                )
            
            if not payment_db.stripe_payment_intent_id:
                return create_problem_response(
                    status_code=400,
                    error_type="bad-request",
                    title="Bad Request",
                    detail="Payment has no Stripe payment intent",
                    instance=str(request.url)
                )
            
            if payment_db.status != PaymentStatus.SUCCEEDED:
                return create_problem_response(
                    status_code=400,
                    error_type="bad-request",
                    title="Bad Request",
                    detail="Only succeeded payments can be refunded",
                    instance=str(request.url)
                )
            
            refund_result = await self.stripe_service.create_refund(
                payment_intent_id=payment_db.stripe_payment_intent_id,
                amount=refund_data.amount,
                reason=refund_data.reason
            )
            
            await self.payment_repo.update_payment_status(payment_db.id, PaymentStatus.REFUNDED)
            
            return {
                "id": refund_result["id"],
                "status": refund_result["status"],
                "amount": refund_result["amount"],
                "currency": refund_result["currency"],
                "reason": refund_result["reason"]
            }
            
        except Exception as e:
            self.logger.error(f"Refund creation failed: {e}")
            return create_problem_response(
                status_code=500,
                error_type="internal-error",
                title="Internal Server Error",
                detail="Failed to create refund",
                instance=str(request.url)
            )