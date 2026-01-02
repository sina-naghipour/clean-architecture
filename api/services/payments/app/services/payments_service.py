from uuid import UUID
import logging
from typing import Optional
from fastapi import Request
import httpx
from opentelemetry import trace
from optl.trace_decorator import trace_service_operation
from datetime import datetime

from database import pydantic_models
from database.database_models import PaymentDB
from repositories.payments_repository import PaymentRepository
from .stripe_service import StripeService
from .notification_service import NotificationService
from .retry_service import RetryService
from .payment_orchestrator import PaymentOrchestrator
from .payment_notification_service import PaymentNotificationService
from .webhook_handler import WebhookHandler
from .refund_processor import RefundProcessor
from cache.redis_cache import cached, invalidate_cache
from .webhook_idempotency import WebhookIdempotencyService
from database.pydantic_models import PaymentStatus

class PaymentService:
    def __init__(self, 
                 logger: logging.Logger, 
                 db_session,
                 stripe_service: StripeService,
                 http_client: Optional[httpx.AsyncClient] = None, redis_cache = None):
        self.logger = logger
        self.tracer = trace.get_tracer(__name__)
        
        self.payment_repo = PaymentRepository(db_session)
        self.stripe_service = stripe_service
        
        notification_service = NotificationService(http_client)
        retry_service = RetryService()
        # self.idempotency_service = WebhookIdempotencyService(redis_cache, logger)

        self.payment_orchestrator = PaymentOrchestrator(self.payment_repo, stripe_service, logger)
        self.payment_notification_service = PaymentNotificationService(notification_service, retry_service, logger)
        self.webhook_handler = WebhookHandler(self.payment_repo, self.tracer, logger)
        self.refund_processor = RefundProcessor(self.payment_repo, stripe_service, logger)
    
    def _to_payment_response(self, payment: PaymentDB) -> pydantic_models.PaymentResponse:
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
            client_secret=payment.client_secret,
            checkout_url=getattr(payment, 'checkout_url', None),
            checkout_session_id=payment.checkout_session_id
        )
    
    @trace_service_operation("create_payment")
    @invalidate_cache(pattern="cache:payment_by_order:*")
    async def create_payment(self, payment_data: pydantic_models.PaymentCreate):
        checkout_mode = getattr(payment_data, 'checkout_mode', True)
        
        payment = await self.payment_orchestrator.create_and_process_payment(
            payment_data, self.tracer, checkout_mode
        )
        self.logger.info(f"Created payment with HEREEEEEEEEEEEE : {self._to_payment_response(payment)}")
        return self._to_payment_response(payment)
    
    @trace_service_operation("get_payment")
    @cached(ttl=300, key_prefix="payment_service")
    async def get_payment(self, payment_id: str):
        with self.tracer.start_as_current_span("get_payment") as span:
            span.set_attribute("payment.id", payment_id)
            
            payment_uuid = UUID(payment_id)
            payment = await self.payment_repo.get_payment_by_id(payment_uuid)
            
            if not payment:
                raise Exception(f"Payment not found: {payment_id}")
            
            return self._to_payment_response(payment)
    
    @trace_service_operation("process_webhook")
    @invalidate_cache(pattern="cache:payment_by_id:*")
    async def process_webhook(self, request: Request, payload: bytes, sig_header: str):
        with self.tracer.start_as_current_span("process_webhook") as span:
            span.set_attributes({
                "http.url": str(request.url),
                "http.method": request.method,
                "client.ip": str(request.client.host) if request.client else "unknown"
            })
            
            event = await self.stripe_service.handle_webhook_event(payload, sig_header)
            event_type = event["type"]
            event_id = event["id"]
            
            async def process_event():
                event_data = event["data"]
                if isinstance(event_data, dict) and "object" in event_data:
                    event_data = event_data["object"]
                
                self.logger.info(f"Processing webhook {event_type} from IP: {request.client.host}")
                span.set_attribute("stripe.event_type", event_type)
                span.set_attribute("stripe.event_id", event_id)
                
                metadata = event_data.get('metadata', {})
                payment_id = metadata.get('payment_id')                
                if not payment_id:
                    self.logger.warning(f"No payment_id in metadata for event: {event_type}")
                    return {"status": "ignored", "reason": "no_payment_id"}
                
                result, receipt_url = await self.webhook_handler.handle_stripe_event(
                    event_type, event_data, UUID(payment_id)
                )
                
                if result and result != "ignored":
                    payment = await self.payment_repo.get_payment_by_id(UUID(payment_id))
                    if payment:
                        self.logger.info(f"HEREE GOT CALEDDDDDDDDDDDDDDDDDDDDDDDDDDDDD : {payment} - {result} - {receipt_url}")
                        await self.payment_notification_service.notify_orders_service(payment, result, receipt_url)
                
                self.logger.info(f"Processed {event_type} for payment ID: {payment_id}")
                return {"status": "processed", "event": event_type}
            
            # COMMENT OUT IDEMPOTENCY FOR NOW
            # try:
            #     result = await self.idempotency_service.handle_event_with_idempotency(
            #         event_id=event_id,
            #         event_type=event_type,
            #         processor_func=process_event
            #     )
            #     
            #     span.set_attribute("webhook.idempotency_status", result.get("status", "unknown"))
            #     
            #     return result
            #     
            # except Exception as e:
            #     self.logger.error(f"Idempotency service error for event {event_id}: {e}")
            #     span.record_exception(e)
            #     span.set_attribute("webhook.idempotency_error", True)
            #     
            #     self.logger.warning(f"Falling back to non-idempotent processing for event {event_id}")
            #     return await process_event()
            
            # DIRECT PROCESSING WITHOUT IDEMPOTENCY
            return await process_event()
        
    @trace_service_operation("create_refund")
    @invalidate_cache(pattern="cache:payment_by_id:*")
    async def create_refund(self, payment_id: str, refund_data: pydantic_models.RefundRequest):
        with self.tracer.start_as_current_span("create_refund") as span:
            span.set_attributes({
                "payment.id": payment_id,
                "refund.amount": float(refund_data.amount) if refund_data.amount else None,
                "refund.reason": refund_data.reason or "unknown"
            })
            
            refund_result = await self.refund_processor.process_refund(payment_id, refund_data)
            
            payment = await self.payment_repo.get_payment_by_id(UUID(payment_id))
            if payment:
                await self.payment_notification_service.notify_orders_service(payment, "refunded")
            
            span.set_attribute("refund.id", refund_result["id"])
            span.set_attribute("refund.status", refund_result["status"])
            
            return refund_result
        
    @trace_service_operation("handle_checkout_success")
    async def handle_checkout_success(self, request):
        """
        Handle successful Stripe Checkout redirect.
        The request object contains the payment_intent_id in its id field.
        """
        return {"status": "success", "message": "Checkout success handled"}
        # with self.tracer.start_as_current_span("handle_checkout_success") as span:
        #     try:
        #         # Extract payment intent ID from request
        #         payment_intent_id = request.get("id")  # This is the key part!
                
        #         if not payment_intent_id:
        #             raise ValueError("No payment_intent_id found in request")
                    
        #         span.set_attribute("stripe.payment_intent_id", payment_intent_id)
        #         self.logger.info(f"Processing successful checkout for payment intent: {payment_intent_id}")
                
        #         # Get payment intent details from Stripe
        #         payment_intent_data = await self.stripe_service.retrieve_payment_intent(payment_intent_id)
                
        #         # Find payment using stripe_payment_intent_id
        #         payment = await self.payment_repo.get_payment_by_stripe_id(payment_intent_id)
                
        #         if payment:
        #             # Update payment status to SUCCEEDED
        #             await self.payment_repo.update_payment_status(payment.id, PaymentStatus.SUCCEEDED)
                    
        #             # Update payment with additional Stripe data if needed
        #             await self.payment_repo.update_stripe_metadata(
        #                 payment.id,
        #                 {
        #                     "stripe_payment_intent_id": payment_intent_id,
        #                     "stripe_payment_intent_status": payment_intent_data.get('status'),
        #                     "stripe_charge_id": payment_intent_data.get('latest_charge'),
        #                     "last_status_update": datetime.utcnow().isoformat(),
        #                     "payment_method": payment_intent_data.get('payment_method'),
        #                     "customer_id": payment_intent_data.get('customer')
        #                 }
        #             )
                    
        #             # Update the order status (assuming you have an order service)
        #             # if hasattr(self, 'order_service'):
        #             #     await self.order_service.update_order_status(
        #             #         payment.order_id, 
        #             #         OrderStatus.PAID  # or whatever your order status enum is
        #             #     )
                    
        #             span.set_attribute("payment.updated", True)
        #             span.set_attribute("payment.id", str(payment.id))
        #             span.set_attribute("order.id", payment.order_id)
        #             self.logger.info(f"Payment {payment_intent_id} updated to SUCCEEDED for order {payment.order_id}")
        #         else:
        #             # Log if payment record not found
        #             self.logger.warning(f"No payment found for Stripe payment intent: {payment_intent_id}")
        #             span.set_attribute("payment.not_found", True)
        #             # You might want to create a payment record here if it doesn't exist
            
        #         return {
        #             "status": "success",
        #             "stripe_payment_intent_id": payment_intent_id,
        #             "payment_intent_status": payment_intent_data.get('status'),
        #             "amount": payment_intent_data.get('amount'),
        #             "currency": payment_intent_data.get('currency'),
        #             "customer_id": payment_intent_data.get('customer'),
        #             "payment_method": payment_intent_data.get('payment_method'),
        #             "message": "Payment completed successfully"
        #         }
        #     except Exception as e:
        #         span.record_exception(e)
        #         self.logger.error(f"Error handling checkout success: {e}")
        #         raise Exception(f"Failed to process checkout success: {str(e)}")

    @trace_service_operation("handle_checkout_cancel")
    async def handle_checkout_cancel(self, request):
        """
        Handle cancelled Stripe Checkout redirect.
        The request object contains the payment_intent_id in its id field.
        """
        return {"status": "cancelled", "message": "Checkout cancel handled"}
        # with self.tracer.start_as_current_span("handle_checkout_cancel") as span:
        #     try:
        #         # Extract payment intent ID from request
        #         payment_intent_id = request.get("id")  # This is the key part!
                
        #         if not payment_intent_id:
        #             raise ValueError("No payment_intent_id found in request")
                    
        #         span.set_attribute("stripe.payment_intent_id", payment_intent_id)
        #         self.logger.info(f"Processing cancelled checkout for payment intent: {payment_intent_id}")
                
        #         # Get payment intent details from Stripe
        #         payment_intent_data = await self.stripe_service.retrieve_payment_intent(payment_intent_id)
                
        #         # Find payment using stripe_payment_intent_id
        #         payment = await self.payment_repo.get_payment_by_stripe_id(payment_intent_id)
                
        #         if payment:
        #             # Update payment status to CANCELED
        #             await self.payment_repo.update_payment_status(payment.id, PaymentStatus.CANCELED)
                    
        #             # Update payment with cancellation metadata
        #             await self.payment_repo.update_stripe_metadata(
        #                 payment.id,
        #                 {
        #                     "stripe_payment_intent_id": payment_intent_id,
        #                     "stripe_payment_intent_status": payment_intent_data.get('status'),
        #                     "cancellation_reason": "user_cancelled",
        #                     "last_status_update": datetime.utcnow().isoformat()
        #                 }
        #             )
                    
        #             # Update the order status
        #             # if hasattr(self, 'order_service'):
        #             #     await self.order_service.update_order_status(
        #             #         payment.order_id, 
        #             #         OrderStatus.CANCELLED  # or whatever your order status enum is
        #             #     )
                    
        #             span.set_attribute("payment.updated", True)
        #             span.set_attribute("payment.id", str(payment.id))
        #             span.set_attribute("order.id", payment.order_id)
        #             self.logger.info(f"Payment {payment_intent_id} updated to CANCELLED for order {payment.order_id}")
        #         else:
        #             self.logger.warning(f"No payment found for Stripe payment intent: {payment_intent_id}")
        #             span.set_attribute("payment.not_found", True)
            
        #         return {
        #             "status": "cancelled",
        #             "stripe_payment_intent_id": payment_intent_id,
        #             "payment_intent_status": payment_intent_data.get('status'),
        #             "amount": payment_intent_data.get('amount'),
        #             "currency": payment_intent_data.get('currency'),
        #             "message": "Payment was cancelled by user"
        #         }
        #     except Exception as e:
        #         span.record_exception(e)
        #         self.logger.error(f"Error handling checkout cancel: {e}")
        #         raise Exception(f"Failed to process checkout cancel: {str(e)}")
            

