# Stage 9 Requirements Analysis (Current State)

| Requirement | Implementation Status | Analysis |
|-------------|----------------------|----------|
| **Stripe Checkout (prebuilt)** | ❌ **Not Implemented** | Your service uses Payment Intents API directly, not Stripe Checkout Sessions |
| **Webhook signature verification** | ⚠️ **Partial Implementation** | Has basic verification but needs more robust handling for production |
| **Idempotency keys** | ⚠️ **Partial Implementation** | Recognized in gRPC but not fully implemented for webhooks |
| **Handle checkout.session.completed** | ❌ **Not Implemented** | Only handles Payment Intent and Charge events |
| **Mark order paid via webhook** | ✅ **Implemented** | Notifies Orders service on successful payment |
| **Affiliate/referral accrual** | ❌ **Not Implemented** | No referral system in the codebase |
| **Referral reporting** | ❌ **Not Implemented** | No reporting endpoints or logic |
| **Basic fraud guards** | ❌ **Not Implemented** | No fraud detection mechanisms |
| **Replay-safe webhook handling** | ⚠️ **Partial Implementation** | Needs idempotency keys for webhook events |
| **Correct referral accrual** | ❌ **Not Implemented** | No referral tracking |
| **Auditable referral logs** | ❌ **Not Implemented** | No audit logging for referrals |
| **create Checkout Session** | ❌ **Not Implemented** | Uses Payment Intents instead of Checkout |
| **verify webhooks** | ⚠️ **Implemented but needs improvement** | Basic verification exists |
| **idempotent updates** | ⚠️ **Partial Implementation** | Mostly via database constraints, not explicit keys |
| **referral-svc/module** | ❌ **Not Implemented** | No referral service or module |
| **Test plan for duplicates** | ❌ **Missing** | No test files included |
| **Test for signature failure** | ❌ **Missing** | No test files included |
| **Test for partial refunds** | ⚠️ **Partially Implemented** | Refund logic exists but no tests |
| **ADR-009 document** | ❌ **Missing** | No ADR documents in bundle |
| **Orders state diff** | ⚠️ **Implemented via webhook** | Orders notified but no state diff mechanism |


we are trying to implement one feature at a time.

## Idempotency Keys

```python
class WebhookIdempotencyService:
    
    def __init__(self, redis_cache, logger: logging.Logger = None):
        self.redis = redis_cache
        self.logger = logger or logging.getLogger(__name__)
        self.EVENT_EXPIRY_DAYS = 7
        self.LOCK_TIMEOUT_SECONDS = 30
    
    async def is_duplicate_event(self, event_id: str) -> bool:
        pass
    
    async def acquire_event_lock(self, event_id: str) -> bool:
        pass
    
    async def release_event_lock(self, event_id: str):
        pass
    
    async def mark_event_processed(self, event_id: str, event_type: str):
        pass
    
    async def handle_event_with_idempotency(self, event_id: str, event_type: str, processor_func):
        pass
```

we use a redis based lock to prevent race conditions for stripe webhooks.

how does this class helps us? it makes sure that each stripe process is done only once.

### Flow

Check if seen → Lock → Re-check → Process → Mark complete → Release lock

so, if webhooks are trying to run simultaneaously, only one instance processes it.



## Webhook Signature Verification

```python
async def handle_webhook_event(self, payload: bytes, sig_header: str) -> Dict[str, Any]:
    
    # 1. Get webhook secret
    webhook_secret = self.webhook_secret
    
    # 2. Always verify signature if secret exists and isn't mock
    if not webhook_secret or webhook_secret == "whsec_mock":
        pass
    try:
        # 3. Verify signature
        
        return
        
    except stripe.error.SignatureVerificationError as e:
        pass
    except Exception as e:
        pass
```


## Stripe Checkout With Backwards Compatibility

```python
class PaymentService:
    def __init__(self, 
                logger: logging.Logger, 
                db_session,
                stripe_service: StripeService,
                commission_service: Optional[CommissionService] = None,
                http_client: Optional[httpx.AsyncClient] = None, redis_cache = None):
        pass
    
    def _to_payment_response(self, payment: PaymentDB) -> pydantic_models.PaymentResponse:
        pass
    
    @trace_service_operation("create_payment")
    @invalidate_cache(pattern="cache:payment_by_order:*")
    async def create_payment(self, payment_data: pydantic_models.PaymentCreate):
        checkout_mode = getattr(payment_data, 'checkout_mode', True)
        
        payment = await self.payment_orchestrator.create_and_process_payment(
            payment_data, self.tracer, checkout_mode
        )
        return self._to_payment_response(payment)
    
    ...

from database import pydantic_models
from database.database_models import PaymentDB, PaymentStatus
from repositories.payments_repository import PaymentRepository
from .stripe_service import StripeService
from opentelemetry import trace
import logging
from .commissions_service import CommissionService
from typing import Optional


class PaymentOrchestrator:
    def __init__(self, payment_repo: PaymentRepository, stripe_service: StripeService, logger: logging.Logger, commission_service: Optional[CommissionService] = None,):
        pass
        
    async def create_and_process_payment(self, payment_data: pydantic_models.PaymentCreate, tracer: trace.Tracer, checkout_mode: bool = True) -> PaymentDB:
        metadata = {
            'order_id': payment_data.order_id,
            'user_id': payment_data.user_id,
            'payment_id': str(created_payment.id),
            'payment_type': 'checkout' if checkout_mode else 'payment_intent',
        }

        if referrer_id:
            metadata['referrer_id'] = referrer_id
        
        stripe_result = await self.stripe_service.create_payment(
            ...
            checkout_mode=checkout_mode,
            ...
        )
        
        if checkout_mode:
            created_payment.checkout_url = stripe_result.get("url")
            await self.payment_repo.update_payment_checkout_url(created_payment.id, stripe_result.get("url"))
            stripe_id = stripe_result.get("payment_intent_id") or stripe_result.get("id")
        else:
            stripe_id = stripe_result.get("id")
            if stripe_result.get("client_secret"):
                await self.payment_repo.update_payment_client_secret(created_payment.id, stripe_result.get("client_secret"))
                created_payment.client_secret = stripe_result.get("client_secret")
        
        if stripe_id:
            await self.payment_repo.update_payment_stripe_id(created_payment.id, stripe_id)
        
        if not checkout_mode:
            payment_status = self.stripe_service.map_stripe_status_to_payment_status(stripe_result["status"])
            created_payment.stripe_payment_intent_id = stripe_id
        else:
            if stripe_result["type"] == "checkout":
                payment_status = PaymentStatus.PROCESSING
                created_payment.checkout_session_id = stripe_result["id"]
                created_payment.stripe_payment_intent_id = None

        await self.payment_repo.update_payment_status(created_payment.id, payment_status)
        return created_payment
```

you could see that we still are able to create a payment using direct api calls, so its a decision that has to be made in orders service.

## Affiliate/ Referrals

referrals was a tricky feature to implement and i've changed my mind throughout implementing this feature many times. but after doing so, i have come to the conclusion that the 
best way to do so is actually the simplest way to do it. we just capture referrer id when we are trying to create an order, and we pass the id to the payments service through grpc.

the other matter was that we had to save commissions table in some service, but where? auth or payments? payments actually made the most sense and was the easiest and most clean way 
to approach this issue.

```python
class CommissionService:
    def __init__(self, commission_repo: CommissionRepository, logger: logging.Logger = None):
        pass

    async def accrue_commission(self, order_id: str, customer_id: str, 
                              amount: float, referrer_id: Optional[str] = None) -> Optional[CommissionDB]:
        self.logger.debug(f"referrer_id: {referrer_id}, customer_id: {customer_id}, order_id: {order_id}, amount: {amount}")
        print(f"referrer_id: {referrer_id}, customer_id: {customer_id}, order_id: {order_id}, amount: {amount}")
        if not referrer_id:  # Guard 1 - no referrer
            return None

        if referrer_id == customer_id:  # Guard 2 - self-referral
            return None

        existing = await self.commission_repo.get_commission_by_order_id(order_id)  # Guard 3 - idempotency
        if existing:
            return existing

        if amount < 1.00:  # Guard 4 - minimum amount
            return None

        commission_amount = Decimal(str(amount)) * self.commission_rate 
        
        audit_log = {
            'calculated_at': datetime.utcnow().isoformat(),
            'order_amount': float(amount),
            'customer_id': customer_id,
            'referrer_id': referrer_id,
            'commission_rate': float(self.commission_rate),
            'fraud_checks_passed': True
        }

        commission = CommissionDB(
            referrer_id=referrer_id,
            order_id=order_id,
            amount=float(commission_amount),
            status='pending',
            audit_log=audit_log
        )


    async def get_report(self, referrer_id: str) -> Dict[str, Any]:
        commissions = await self.commission_repo.get_commissions_by_referrer(referrer_id)
        
        total_commissions = sum(c.amount for c in commissions)
        pending = sum(c.amount for c in commissions if c.status == 'pending')
        paid = sum(c.amount for c in commissions if c.status == 'paid')
        
        return {
            'referrer_id': referrer_id,
            'total_commissions': len(commissions),
            'total_amount': total_commissions,
            'pending_amount': pending,
            'paid_amount': paid,
            'commissions': [
                {
                    'id': str(c.id),
                    'order_id': c.order_id,
                    'amount': c.amount,
                    'status': c.status,
                    'created_at': c.created_at.isoformat()
                }
                for c in commissions
            ]
        }

    async def mark_commission_paid(self, commission_id: str) -> Optional[CommissionDB]:
        try:
            return await self.commission_repo.update_commission_status(uuid.UUID(commission_id), 'paid')
        except Exception as e:
            self.logger.error(f"Failed to mark commission as paid: {e}")
            return None
```

