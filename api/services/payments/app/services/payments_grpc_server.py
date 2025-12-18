import grpc.aio
import asyncio
import logging

from protos import payments_pb2, payments_pb2_grpc
from database import pydantic_models


class PaymentGRPCServer(payments_pb2_grpc.PaymentServiceServicer):
    def __init__(self, payment_service, logger: logging.Logger):
        self.payment_service = payment_service
        self.logger = logger
    
    async def CreatePayment(self, request, context):
        try:
            self.logger.info(f"gRPC CreatePayment for order: {request.order_id}")
            
            payment_data = pydantic_models.PaymentCreate(
                order_id=request.order_id,
                amount=request.amount,
                user_id=request.user_id,
                payment_method_token=request.payment_method_token,
                currency=request.currency or "usd",
                metadata=dict(request.metadata) if request.metadata else None
            )
            
            result = await self.payment_service.create_payment(payment_data)
            
            # Convert all fields to proper types for protobuf
            return payments_pb2.PaymentResponse(
                payment_id=str(result.id),
                order_id=str(result.order_id),
                user_id=str(result.user_id),
                amount=float(result.amount),
                status=str(result.status.value),
                stripe_payment_intent_id=str(result.stripe_payment_intent_id or ""),
                payment_method_token=str(result.payment_method_token or ""),
                currency=str(result.currency or "usd"),
                client_secret=""
            )
            
        except Exception as e:
            self.logger.error(f"gRPC CreatePayment failed: {e}", exc_info=True)
            await context.abort(grpc.StatusCode.INTERNAL, str(e))
    
    async def GetPayment(self, request, context):
        try:
            self.logger.info(f"gRPC GetPayment: {request.payment_id}")
            
            result = await self.payment_service.get_payment(request.payment_id)
            
            # Convert all fields to proper types for protobuf
            return payments_pb2.PaymentResponse(
                payment_id=str(result.id),
                order_id=str(result.order_id),
                user_id=str(result.user_id),
                amount=float(result.amount),
                status=str(result.status.value),
                stripe_payment_intent_id=str(result.stripe_payment_intent_id or ""),
                payment_method_token=str(result.payment_method_token or ""),
                currency=str(result.currency or "usd"),
                client_secret=""
            )
            
        except Exception as e:
            self.logger.error(f"gRPC GetPayment failed: {e}", exc_info=True)
            if "not found" in str(e).lower():
                await context.abort(grpc.StatusCode.NOT_FOUND, str(e))
            else:
                await context.abort(grpc.StatusCode.INTERNAL, str(e))
    
    async def ProcessRefund(self, request, context):
        try:
            self.logger.info(f"gRPC ProcessRefund: {request.payment_id}")
            
            refund_data = pydantic_models.RefundRequest(
                amount=request.amount if request.amount > 0 else None,
                reason=request.reason or None
            )
            
            result = await self.payment_service.create_refund(request.payment_id, refund_data)
            
            return payments_pb2.RefundResponse(
                refund_id=str(result["id"]),
                status=str(result["status"]),
                amount=float(result["amount"]),
                currency=str(result["currency"]),
                reason=str(result.get("reason", ""))
            )
            
        except Exception as e:
            self.logger.error(f"gRPC ProcessRefund failed: {e}", exc_info=True)
            await context.abort(grpc.StatusCode.INTERNAL, str(e))


async def serve_grpc(payment_service, host: str = "0.0.0.0", port: int = 50051):
    logger = logging.getLogger(__name__)
    
    server = grpc.aio.server()
    
    payments_pb2_grpc.add_PaymentServiceServicer_to_server(
        PaymentGRPCServer(payment_service, logger), server
    )
    
    server_address = f"{host}:{port}"
    server.add_insecure_port(server_address)
    
    logger.info(f"Async gRPC server started on {server_address}")
    await server.start()
    
    try:
        await server.wait_for_termination()
    except KeyboardInterrupt:
        await server.stop(5)