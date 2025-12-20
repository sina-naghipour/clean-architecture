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
from optl.trace_decorator import trace_service_operation
from opentelemetry import trace

class PaymentService:
    def __init__(self, logger: logging.Logger, db_session):
        self.logger = logger
        self.payment_repo = PaymentRepository(db_session)
        self.stripe_service = StripeService(logger)
        self.orders_webhook_url = os.getenv("ORDERS_WEBHOOK_URL", "http://orders:8002/webhooks/payment-updates")
        self.internal_api_key = os.getenv("INTERNAL_API_KEY", "default_internal_key")
        self.tracer = trace.get_tracer(__name__)
    
    @trace_service_operation("notify_orders_service")
    async def _notify_orders_service(self, payment_id: UUID, status: str, receipt_url: str = None):
        try:
            with self.tracer.start_as_current_span("notify_orders_service") as span:
                span.set_attributes({
                    "payment.id": str(payment_id),
                    "payment.status": status,
                    "webhook.url": self.orders_webhook_url
                })
                
                payment = await self.payment_repo.get_payment_by_id(payment_id)
                if not payment or not payment.order_id:
                    span.set_attribute("notification.skipped", True)
                    return False

                max_retries = 3
                base_delay = 1.0
                
                for attempt in range(max_retries):
                    span.set_attribute("retry.attempt", attempt + 1)
                    
                    try:
                        idempotency_key = f"payment_{payment_id}_{status}_{int(time.time())}"
                        span.set_attribute("idempotency.key", idempotency_key)
                        
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
                            
                            span.set_attribute("http.status_code", response.status_code)
                            
                            if response.status_code == 200:
                                self.logger.info(f"Notified Orders service for payment {payment_id}")
                                span.set_attribute("notification.success", True)
                                return True
                            else:
                                self.logger.error(f"Failed to notify Orders: {response.status_code}")
                        
                        if attempt < max_retries - 1:
                            delay = base_delay * (2 ** attempt)
                            span.set_attribute("retry.delay", delay)
                            self.logger.info(f"Retrying in {delay}s...")
                            await asyncio.sleep(delay)
                            continue
                            
                    except Exception as e:
                        span.record_exception(e)
                        self.logger.warning(f"Attempt {attempt + 1} failed: {e}")
                        if attempt < max_retries - 1:
                            delay = base_delay * (2 ** attempt)
                            await asyncio.sleep(delay)
                            continue
                            
        except Exception as e:
            span = trace.get_current_span()
            span.record_exception(e)
            self.logger.warning(f"Could not notify Orders service: {e}")
        
        return False

    @trace_service_operation("create_payment")
    async def create_payment(self, payment_data: pydantic_models.PaymentCreate):
        with self.tracer.start_as_current_span("create_payment") as span:
            span.set_attributes({
                "order.id": payment_data.order_id,
                "user.id": payment_data.user_id,
                "amount": float(payment_data.amount),
                "currency": payment_data.currency
            })
            
            existing_payment = await self.payment_repo.get_payment_by_order_id(payment_data.order_id)
            if existing_payment:
                span.set_attribute("payment.exists", True)
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
            span.set_attribute("payment.id", str(created_payment.id))
            
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
                
                span.set_attribute("stripe.id", stripe_result["id"])
                span.set_attribute("payment.status", str(payment_status.value))
                
            except Exception as e:
                span.record_exception(e)
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
    
    @trace_service_operation("get_payment")
    async def get_payment(self, payment_id: str):
        with self.tracer.start_as_current_span("get_payment") as span:
            span.set_attribute("payment.id", payment_id)
            
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
    
    @trace_service_operation("process_webhook")
    async def process_webhook(self, request: Request, payload: bytes, sig_header: str):
        with self.tracer.start_as_current_span("process_webhook") as span:
            span.set_attributes({
                "http.url": str(request.url),
                "http.method": request.method,
                "client.ip": str(request.client.host) if request.client else "unknown"
            })
            
            event = await self.stripe_service.handle_webhook_event(payload, sig_header)
            event_type = event["type"]
            event_data = event["data"]
            
            if isinstance(event_data, dict) and "object" in event_data:
                event_data = event_data["object"]
            
            self.logger.info(f"Processing webhook {event_type} from IP: {request.client.host}")
            span.set_attribute("stripe.event_type", event_type)
            
            metadata = event_data.get('metadata', {})
            payment_id = metadata.get('payment_id')
            
            if not payment_id:
                self.logger.warning(f"No payment_id in metadata for event: {event_type}")
                return {"status": "ignored", "reason": "no_payment_id"}
            
            payment = await self.payment_repo.get_payment_by_id(UUID(payment_id))
            
            if not payment:
                self.logger.warning(f"Payment not found: {payment_id}")
                return {"status": "ignored", "reason": "payment_not_found"}
            
            span.set_attribute("payment.id", payment_id)
            
            if event_type.startswith("payment_intent."):
                stripe_status = event_data.get("status")
                                
                if event_type == "payment_intent.payment_failed":
                    await self.payment_repo.update_payment_status(payment.id, PaymentStatus.FAILED)
                    await self._notify_orders_service(payment.id, "failed")
                    span.set_attribute("payment.new_status", "FAILED")
                    
                elif event_type == "payment_intent.created":
                    await self.payment_repo.update_payment_status(payment.id, PaymentStatus.CREATED)
                    if event_data.get("client_secret"):
                        await self.payment_repo.update_payment_client_secret(payment.id, event_data.get("client_secret"))
                    span.set_attribute("payment.new_status", "CREATED")
                        
                elif event_type == "payment_intent.canceled":
                    await self.payment_repo.update_payment_status(payment.id, PaymentStatus.CANCELED)
                    await self._notify_orders_service(payment.id, "canceled")
                    span.set_attribute("payment.new_status", "CANCELED")
            
            elif event_type.startswith("charge."):
                charge_status = event_data.get("status")
                
                if event_type == "charge.refunded":
                    await self.payment_repo.update_payment_status(payment.id, PaymentStatus.REFUNDED)
                    await self._notify_orders_service(payment.id, "refunded")
                    span.set_attribute("payment.new_status", "REFUNDED")
                    
                elif event_type in ["charge.succeeded"]:
                    if charge_status == "succeeded":
                        receipt_url = event_data.get("receipt_url")
                        
                        await self.payment_repo.update_payment_status(payment.id, PaymentStatus.SUCCEEDED)
                        await self._notify_orders_service(payment.id, "succeeded", receipt_url)
                        span.set_attribute("payment.new_status", "SUCCEEDED")
            
            self.logger.info(f"Processed {event_type} for payment ID: {payment_id}")
            return {"status": "processed", "event": event_type}
    
    @trace_service_operation("create_refund")
    async def create_refund(self, payment_id: str, refund_data: pydantic_models.RefundRequest):
        with self.tracer.start_as_current_span("create_refund") as span:
            span.set_attributes({
                "payment.id": payment_id,
                "refund.amount": float(refund_data.amount) if refund_data.amount else None,
                "refund.reason": refund_data.reason or "unknown"
            })
            
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
            
            span.set_attribute("refund.id", refund_result["id"])
            span.set_attribute("refund.status", refund_result["status"])
            
            return {
                "id": refund_result["id"],
                "status": refund_result["status"],
                "amount": refund_result["amount"],
                "currency": refund_result["currency"],
                "reason": refund_result["reason"]
            }