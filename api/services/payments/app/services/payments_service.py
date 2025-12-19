from .stripe_service import StripeService
from database import pydantic_models
from uuid import UUID
from repositories.payments_repository import PaymentRepository
from database.database_models import PaymentDB, PaymentStatus
import logging
from fastapi import Request
import httpx
import os
import asyncio
import time

class PaymentService:
    def __init__(self, logger: logging.Logger, db_session):
        self.logger = logger
        self.payment_repo = PaymentRepository(db_session)
        self.stripe_service = StripeService(logger)
        self.orders_webhook_url = os.getenv("ORDERS_WEBHOOK_URL", "http://orders:8002/webhooks/payment-updates")
        self.internal_api_key = os.getenv("INTERNAL_API_KEY", "default_internal_key")
    
    async def _notify_orders_service(self, payment_id: UUID, status: str, receipt_url: str = None):
        try:
            payment = await self.payment_repo.get_payment_by_id(payment_id)
            if not payment or not payment.order_id:
                return False

            max_retries = 3
            base_delay = 1.0
            
            for attempt in range(max_retries):
                try:
                    idempotency_key = f"payment_{payment_id}_{status}_{int(time.time())}"
                    
                    async with httpx.AsyncClient() as client:
                        response = await client.post(
                            self.orders_webhook_url,
                            json={
                                "order_id": payment.order_id,
                                "payment_id": str(payment.id),
                                "status": status,
                                "stripe_payment_intent_id": payment.stripe_payment_intent_id,
                                "receipt_url": receipt_url
                            },
                            headers={
                                "X-API-Key": self.internal_api_key,
                                "X-Idempotency-Key": idempotency_key
                            },
                            timeout=5.0
                        )
                        
                        if response.status_code == 200:
                            self.logger.info(f"Notified Orders service for payment {payment_id}")
                            return True
                        else:
                            self.logger.error(f"Failed to notify Orders: {response.status_code}")
                            
                    # Exponential backoff before retry
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt)  # 1s, 2s, 4s
                        self.logger.info(f"Retrying in {delay}s...")
                        await asyncio.sleep(delay)
                        continue
                        
                except Exception as e:
                    self.logger.warning(f"Attempt {attempt + 1} failed: {e}")
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt)
                        await asyncio.sleep(delay)
                        continue
                        
        except Exception as e:
            self.logger.warning(f"Could not notify Orders service: {e}")
        
        return False
    async def create_payment(self, payment_data: pydantic_models.PaymentCreate):
        existing_payment = await self.payment_repo.get_payment_by_order_id(payment_data.order_id)
        if existing_payment:
            return pydantic_models.PaymentResponse(
                id=str(existing_payment.id),
                order_id=existing_payment.order_id,
                user_id=existing_payment.user_id,
                amount=existing_payment.amount,
                status=existing_payment.status,
                stripe_payment_intent_id=existing_payment.stripe_payment_intent_id,
                payment_method_token=existing_payment.payment_method_token,
                currency=existing_payment.currency,
                created_at=existing_payment.created_at.isoformat(),
                updated_at=existing_payment.updated_at.isoformat(),
                client_secret=existing_payment.client_secret
            )
        
        payment = PaymentDB(
            order_id=payment_data.order_id,
            user_id=payment_data.user_id,
            amount=payment_data.amount,
            payment_method_token=payment_data.payment_method_token,
            currency=payment_data.currency,
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
            await self.payment_repo.update_payment_client_secret(created_payment.id, stripe_result.get("client_secret"))
            created_payment.client_secret = stripe_result.get("client_secret")
            
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
            created_at=created_payment.created_at.isoformat(),
            updated_at=created_payment.updated_at.isoformat(),
            client_secret=created_payment.client_secret
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
            created_at=payment.created_at.isoformat(),
            updated_at=payment.updated_at.isoformat(),            
        )
    
    async def process_webhook(self, request: Request, payload: bytes, sig_header: str):
        event = await self.stripe_service.handle_webhook_event(payload, sig_header)
        event_type = event["type"]
        
        event_data = event["data"]
        
        if isinstance(event_data, dict) and "object" in event_data:
            event_data = event_data["object"]
        
        self.logger.info(f"Processing webhook {event_type} from IP: {request.client.host}")
        
        metadata = event_data.get('metadata', {})
        payment_id = metadata.get('payment_id')
        
        if not payment_id:
            self.logger.warning(f"No payment_id in metadata for event: {event_type}")
            return {"status": "ignored", "reason": "no_payment_id"}
        
        payment = await self.payment_repo.get_payment_by_id(UUID(payment_id))
        
        if not payment:
            self.logger.warning(f"Payment not found: {payment_id}")
            return {"status": "ignored", "reason": "payment_not_found"}
        
        if event_type.startswith("payment_intent."):
            stripe_status = event_data.get("status")
                            
            if event_type == "payment_intent.payment_failed":
                print('event-> failed')
                await self.payment_repo.update_payment_status(payment.id, PaymentStatus.FAILED)
                await self._notify_orders_service(payment.id, "failed")
                
            elif event_type == "payment_intent.created":
                print('event-> created')
                await self.payment_repo.update_payment_status(payment.id, PaymentStatus.CREATED)
                if event_data.get("client_secret"):
                    await self.payment_repo.update_payment_client_secret(payment.id, event_data.get("client_secret"))
                    
            elif event_type == "payment_intent.canceled":
                print('event-> canceled')
                await self.payment_repo.update_payment_status(payment.id, PaymentStatus.CANCELED)
                await self._notify_orders_service(payment.id, "canceled")
        
        elif event_type.startswith("charge."):
            charge_status = event_data.get("status")
            
            if event_type == "charge.refunded":
                print(f"EVENT CAUGHT: {event_type} - Payment ID: {payment.id}")
                await self.payment_repo.update_payment_status(payment.id, PaymentStatus.REFUNDED)
                await self._notify_orders_service(payment.id, "refunded")
                
            elif event_type in ["charge.succeeded"]:
                if charge_status == "succeeded":
                    receipt_url = event_data.get("receipt_url")
                    
                    await self.payment_repo.update_payment_status(payment.id, PaymentStatus.SUCCEEDED)
                    await self._notify_orders_service(payment.id, "succeeded", receipt_url)
                    
        self.logger.info(f"Processed {event_type} for payment ID: {payment_id}")
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
        await self._notify_orders_service(payment.id, "refunded")
        
        return {
            "id": refund_result["id"],
            "status": refund_result["status"],
            "amount": refund_result["amount"],
            "currency": refund_result["currency"],
            "reason": refund_result["reason"]
        }