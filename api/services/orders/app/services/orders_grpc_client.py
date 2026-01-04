from protos import payments_pb2, payments_pb2_grpc
import grpc.aio
import os
import asyncio
import time
from typing import Optional
from optl.trace_decorator import trace_service_operation
from opentelemetry import trace
import logging
class PaymentGRPCClient:
    def __init__(self,  logger: logging.Logger):
        self.host = os.getenv("PAYMENTS_GRPC_HOST", "payments")
        self.port = int(os.getenv("PAYMENTS_GRPC_PORT", "50051"))
        self.logger = logger
        self.channel = None
        self.initialized = False
        self.failure_count = 0
        self.circuit_open = False
        self.circuit_open_until = 0
        self.max_retries = 3
        self.tracer = trace.get_tracer(__name__)
    
    async def initialize(self):
        if not self.initialized:
            server_address = f"{self.host}:{self.port}"
            self.channel = grpc.aio.insecure_channel(server_address)
            self.initialized = True
    
    def _should_try_request(self) -> bool:
        if self.circuit_open:
            if time.time() < self.circuit_open_until:
                return False
            else:
                self.circuit_open = False
                self.failure_count = 0
                return True
        return True
    
    def _record_failure(self):
        self.failure_count += 1
        if self.failure_count >= 5:
            self.circuit_open = True
            self.circuit_open_until = time.time() + 30
    
    def _record_success(self):
        self.failure_count = 0
        self.circuit_open = False
    
    @trace_service_operation("create_payment_grpc")
    async def create_payment(self, order_id, amount, user_id, payment_method_token, 
                            checkout_mode=False, success_url=None, cancel_url=None, referral_code=None):
        if not self.initialized:
            await self.initialize()
        idempotency_key = f"create_{order_id}_{int(time.time())}"
        
        for attempt in range(self.max_retries):
            if not self._should_try_request():
                raise Exception("Circuit breaker open - payments service unavailable")
            
            try:
                with self.tracer.start_as_current_span(f"grpc-payment-attempt-{attempt+1}") as span:
                    span.set_attributes({
                        "grpc.service": "PaymentService",
                        "grpc.method": "CreatePayment",
                        "grpc.attempt": attempt + 1,
                        "order.id": str(order_id),
                        "user.id": str(user_id),
                        "amount": float(amount),
                        "checkout.mode": checkout_mode,
                        "idempotency_key": idempotency_key
                    })
                    
                    stub = payments_pb2_grpc.PaymentServiceStub(self.channel)
                    
                    request_kwargs = {
                        "order_id": order_id,
                        "user_id": user_id,
                        "amount": amount,
                        "payment_method_token": payment_method_token,
                        "currency": "usd",
                        "referral_code": referral_code
                    }
                    
                    if success_url:
                        request_kwargs["success_url"] = success_url
                    if cancel_url:
                        request_kwargs["cancel_url"] = cancel_url
                    if not checkout_mode:
                        request_kwargs["checkout_mode"] = checkout_mode
                    
                    request = payments_pb2.CreatePaymentRequest(**request_kwargs)
                    
                    metadata = (('idempotency-key', idempotency_key),)
                    response = await stub.CreatePayment(request, metadata=metadata, timeout=10)
                    self._record_success()
                    span.set_attribute("grpc.success", True)
                    span.set_attribute("payment.id", response.payment_id)
                    return response
                    
            except grpc.RpcError as e:
                self._record_failure()
                if e.code() == grpc.StatusCode.ALREADY_EXISTS:
                    raise Exception(f"Payment already exists for order: {order_id}")
                
                if attempt < self.max_retries - 1:
                    delay = 1.0 * (2 ** attempt)
                    await asyncio.sleep(delay)
                    continue
                raise
            except Exception as e:
                self._record_failure()
                if attempt < self.max_retries - 1:
                    delay = 1.0 * (2 ** attempt)
                    await asyncio.sleep(delay)
                continue
                raise

    @trace_service_operation("get_payment_grpc")
    async def get_payment(self, payment_id):
        if not self.initialized:
            await self.initialize()
        
        if not self._should_try_request():
            raise Exception("Circuit breaker open - payments service unavailable")
        
        try:
            with self.tracer.start_as_current_span("grpc-get-payment") as span:
                span.set_attributes({
                    "grpc.service": "PaymentService",
                    "grpc.method": "GetPayment",
                    "payment.id": str(payment_id),
                })
                
                stub = payments_pb2_grpc.PaymentServiceStub(self.channel)
                request = payments_pb2.GetPaymentRequest(payment_id=payment_id)
                
                response = await stub.GetPayment(request, timeout=5)
                self._record_success()
                
                span.set_attribute("grpc.success", True)
                span.set_attribute("payment.status", response.status)
                return {
                    "id": response.payment_id,
                    "order_id": response.order_id,
                    "user_id": response.user_id,
                    "amount": response.amount,
                    "status": response.status,
                    "stripe_payment_intent_id": response.stripe_payment_intent_id,
                    "payment_method_token": response.payment_method_token,
                    "currency": response.currency,
                    "client_secret": response.client_secret,
                    "checkout_url": response.checkout_url if response.checkout_url else None
                }
                
        except grpc.RpcError as e:
            self._record_failure()
            span = trace.get_current_span()
            span.set_attribute("grpc.error_code", e.code().name)
            span.set_attribute("grpc.error_details", e.details()[:100])
            raise   
    async def close(self):
        if self.channel:
            await self.channel.close()
            self.initialized = False
            self.channel = None