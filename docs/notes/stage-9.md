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

