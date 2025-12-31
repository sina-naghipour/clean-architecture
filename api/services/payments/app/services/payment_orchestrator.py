from database import pydantic_models
from database.database_models import PaymentDB, PaymentStatus
from repositories.payments_repository import PaymentRepository
from .stripe_service import StripeService
from opentelemetry import trace


class PaymentOrchestrator:
    def __init__(self, payment_repo: PaymentRepository, stripe_service: StripeService):
        self.payment_repo = payment_repo
        self.stripe_service = stripe_service
    
    async def create_and_process_payment(self, payment_data: pydantic_models.PaymentCreate, tracer: trace.Tracer) -> PaymentDB:
        with tracer.start_as_current_span("create_and_process_payment") as span:
            span.set_attributes({
                "order.id": payment_data.order_id,
                "user.id": payment_data.user_id,
                "amount": float(payment_data.amount),
                "currency": payment_data.currency
            })
            
            existing_payment = await self.payment_repo.get_payment_by_order_id(payment_data.order_id)
            if existing_payment:
                span.set_attribute("payment.exists", True)
                return existing_payment
            
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
                
                if stripe_result.get("client_secret"):
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
            
            return created_payment