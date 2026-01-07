import grpc.aio
import asyncio
import logging

from protos import payments_pb2, payments_pb2_grpc
from database import pydantic_models
from optl.trace_decorator import trace_service_operation
from opentelemetry import trace

from protos import commissions_pb2, commissions_pb2_grpc

class PaymentGRPCServer(payments_pb2_grpc.PaymentServiceServicer, commissions_pb2_grpc.CommissionServiceServicer):
    def __init__(self, payment_service, commission_service, logger: logging.Logger):
        self.payment_service = payment_service
        self.commission_service = commission_service
        self.logger = logger
        self.tracer = trace.get_tracer(__name__)

    @trace_service_operation("grpc_create_payment")
    async def CreatePayment(self, request, context):
        try:
            with self.tracer.start_as_current_span("grpc.CreatePayment") as span:
                span.set_attributes({
                    "grpc.method": "CreatePayment",
                    "grpc.service": "PaymentService",
                    "order.id": str(request.order_id),
                    "user.id": str(request.user_id),
                    "amount": float(request.amount),
                    "checkout.mode": request.checkout_mode if request.HasField("checkout_mode") else True,
                    "referrer_id": request.referrer_id if request.HasField("referrer_id") else None
                })
                
                self.logger.info(f"gRPC CreatePayment for order: {request.order_id}")
                
                metadata = dict(context.invocation_metadata())
                idempotency_key = metadata.get('idempotency-key')
                
                if idempotency_key:
                    span.set_attribute("idempotency.key", idempotency_key)
                    self.logger.info(f"CreatePayment with idempotency key: {idempotency_key}")

                existing_payment = await self.payment_service.payment_repo.get_payment_by_order_id(request.order_id)
                if existing_payment:
                    span.set_attribute("payment.exists", True)

                    result = await self.payment_service.get_payment(str(existing_payment.id))
                    client_secret = "NONE" if request.checkout_mode else result.client_secret
                    return payments_pb2.PaymentResponse(
                        payment_id=str(result.id),
                        order_id=str(result.order_id),
                        user_id=str(result.user_id),
                        amount=float(result.amount),
                        status=str(result.status.value),
                        stripe_payment_intent_id=str(result.stripe_payment_intent_id or ""),
                        payment_method_token=str(result.payment_method_token or ""),
                        currency=str(result.currency or "usd"),
                        client_secret=client_secret or "",
                        checkout_url=result.checkout_url or "" if hasattr(result, 'checkout_url') else ""
                    )

                checkout_mode = request.checkout_mode if request.HasField("checkout_mode") else True
                success_url = request.success_url if request.HasField("success_url") else None
                cancel_url = request.cancel_url if request.HasField("cancel_url") else None
                
                
                payment_data_dict = {
                    "order_id": request.order_id,
                    "amount": request.amount,
                    "user_id": request.user_id,
                    "payment_method_token": request.payment_method_token,
                    "currency": request.currency or "usd",
                    "checkout_mode": checkout_mode,
                    "success_url": success_url,
                    "cancel_url": cancel_url,
                    "metadata": dict(request.metadata) if request.metadata else None
                }
                payment_data_dict["referrer_id"] = request.referrer_id
                payment_data = pydantic_models.PaymentCreate(**payment_data_dict)
                result = await self.payment_service.create_payment(payment_data)
                span.set_attribute("payment.id", str(result.id))
                span.set_attribute("payment.status", str(result.status.value))
                
                checkout_url = getattr(result, 'checkout_url', None) or ""
                client_secret = "NONE" if checkout_mode else result.client_secret
                response = payments_pb2.PaymentResponse(
                    payment_id=str(result.id),
                    order_id=str(result.order_id),
                    user_id=str(result.user_id),
                    amount=float(result.amount),
                    status=str(result.status.value),
                    stripe_payment_intent_id=str(result.stripe_payment_intent_id or ""),
                    payment_method_token=str(result.payment_method_token or ""),
                    currency=str(result.currency or "usd"),
                    client_secret=client_secret or "",
                    checkout_url=checkout_url,
                )
                return response

        except Exception as e:
            span = trace.get_current_span()
            span.record_exception(e)
            span.set_attribute("grpc.error", True)
            self.logger.error(f"gRPC CreatePayment failed: {e}", exc_info=True)
            await context.abort(grpc.StatusCode.INTERNAL, str(e))

    @trace_service_operation("grpc_get_payment")
    async def GetPayment(self, request, context):
        try:
            with self.tracer.start_as_current_span("grpc.GetPayment") as span:
                span.set_attributes({
                    "grpc.method": "GetPayment",
                    "grpc.service": "PaymentService",
                    "payment.id": str(request.payment_id)
                })
                
                self.logger.info(f"gRPC GetPayment: {request.payment_id}")
                
                result = await self.payment_service.get_payment(request.payment_id)
                span.set_attribute("payment.status", str(result.status.value))
                
                checkout_url = getattr(result, 'checkout_url', None) or ""
                return payments_pb2.PaymentResponse(
                    payment_id=str(result.id),
                    order_id=str(result.order_id),
                    user_id=str(result.user_id),
                    amount=float(result.amount),
                    status=str(result.status.value),
                    stripe_payment_intent_id=str(result.stripe_payment_intent_id or ""),
                    payment_method_token=str(result.payment_method_token or ""),
                    currency=str(result.currency or "usd"),
                    client_secret=result.client_secret or "",
                    checkout_url=checkout_url
                )
                
        except Exception as e:
            span = trace.get_current_span()
            span.record_exception(e)
            span.set_attribute("grpc.error", True)
            self.logger.error(f"gRPC GetPayment failed: {e}", exc_info=True)
            if "not found" in str(e).lower():
                await context.abort(grpc.StatusCode.NOT_FOUND, str(e))
            else:
                await context.abort(grpc.StatusCode.INTERNAL, str(e))
    
    @trace_service_operation("grpc_process_refund")
    async def ProcessRefund(self, request, context):
        try:
            with self.tracer.start_as_current_span("grpc.ProcessRefund") as span:
                span.set_attributes({
                    "grpc.method": "ProcessRefund",
                    "grpc.service": "PaymentService",
                    "payment.id": str(request.payment_id),
                    "refund.amount": float(request.amount)
                })
                
                self.logger.info(f"gRPC ProcessRefund: {request.payment_id}")
                
                refund_data = pydantic_models.RefundRequest(
                    amount=request.amount if request.amount > 0 else None,
                    reason=request.reason or None
                )
                
                result = await self.payment_service.create_refund(request.payment_id, refund_data)
                span.set_attribute("refund.id", str(result["id"]))
                span.set_attribute("refund.status", str(result["status"]))
                
                return payments_pb2.RefundResponse(
                    refund_id=str(result["id"]),
                    status=str(result["status"]),
                    amount=float(result["amount"]),
                    currency=str(result["currency"]),
                    reason=str(result.get("reason", ""))
                )
                
        except Exception as e:
            span = trace.get_current_span()
            span.record_exception(e)
            span.set_attribute("grpc.error", True)
            self.logger.error(f"gRPC ProcessRefund failed: {e}", exc_info=True)
            await context.abort(grpc.StatusCode.INTERNAL, str(e))

    @trace_service_operation("grpc_get_commission_report")
    async def GetCommissionReport(self, request, context):
        try:
            with self.tracer.start_as_current_span("grpc.GetCommissionReport") as span:
                span.set_attributes({
                    "grpc.method": "GetCommissionReport",
                    "grpc.service": "CommissionService",
                    "referrer.id": str(request.referrer_id)
                })
                
                self.logger.info(f"gRPC GetCommissionReport for referrer: {request.referrer_id}")
                
                report_dict = await self.commission_service.get_report(request.referrer_id)
                
                return commissions_pb2.CommissionReport(
                    referrer_id=report_dict['referrer_id'],
                    total_commissions=report_dict['total_commissions'],
                    total_amount=report_dict['total_amount'],
                    pending_amount=report_dict['pending_amount'],
                    paid_amount=report_dict['paid_amount'],
                    commissions=[
                        commissions_pb2.Commission(
                            id=c['id'],
                            order_id=c['order_id'],
                            amount=c['amount'],
                            status=c['status'],
                            created_at=c['created_at']
                        ) for c in report_dict['commissions']
                    ]
                )
                
        except Exception as e:
            span = trace.get_current_span()
            span.record_exception(e)
            span.set_attribute("grpc.error", True)
            self.logger.error(f"gRPC GetCommissionReport failed: {e}", exc_info=True)
            await context.abort(grpc.StatusCode.INTERNAL, str(e))

@trace_service_operation("serve_grpc")
async def serve_grpc(payment_service, commission_service, host: str = "0.0.0.0", port: int = 50051):
    logger = logging.getLogger(__name__)
    
    server = grpc.aio.server()
    
    server.add_generic_rpc_handlers((
        payments_pb2_grpc.add_PaymentServiceServicer_to_server(
            PaymentGRPCServer(payment_service, commission_service, logger), server
        ),
        commissions_pb2_grpc.add_CommissionServiceServicer_to_server(
            PaymentGRPCServer(payment_service, commission_service, logger), server
        )
    ))
    
    server_address = f"{host}:{port}"
    server.add_insecure_port(server_address)
    
    logger.info(f"Async gRPC server started on {server_address}")
    await server.start()
    
    try:
        await server.wait_for_termination()
    except KeyboardInterrupt:
        await server.stop(5)