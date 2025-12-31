from dataclasses import dataclass
from typing import Optional
import grpc
import asyncio

@dataclass
class PaymentResult:
    payment_id: str
    client_secret: str
    success: bool
    error: Optional[str] = None

class PaymentProcessingError(Exception):
    pass

class PaymentServiceUnavailableError(Exception):
    pass

class PaymentOrchestrator:
    def __init__(self, payment_client, circuit_breaker, logger):
        self.payment_client = payment_client
        self.circuit_breaker = circuit_breaker
        self.logger = logger

    async def process_payment(self, order_id: str, amount: float,
                            user_id: str, payment_method_token: str) -> PaymentResult:
        if self.circuit_breaker.is_open():
            raise PaymentServiceUnavailableError("Circuit breaker open")

        try:
            payment = await self._retry_payment_creation(
                order_id, amount, user_id, payment_method_token
            )
            self.circuit_breaker.record_success()
            return PaymentResult(
                payment_id=payment.payment_id,
                client_secret=payment.client_secret,
                success=True
            )
        except Exception as e:
            self.circuit_breaker.record_failure()
            raise PaymentProcessingError(f"Payment failed: {str(e)}")

    async def _retry_payment_creation(self, order_id, amount, user_id, payment_method_token):
        for attempt in range(3):
            try:
                return await self.payment_client.create_payment(
                    order_id=order_id,
                    amount=amount,
                    user_id=user_id,
                    payment_method_token=payment_method_token
                )
            except grpc.RpcError as e:
                if attempt == 2:
                    raise
                delay = 2 ** attempt
                await asyncio.sleep(delay)