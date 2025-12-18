import grpc
from concurrent import futures
import logging

from protos import payments_pb2, payments_pb2_grpc
from database import pydantic_models


class PaymentGRPCServer(payments_pb2_grpc.PaymentServiceServicer):
    def __init__(self, payment_service, logger: logging.Logger):
        self.payment_service = payment_service
        self.logger = logger
    
    def CreatePayment(self, request, context):
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
            
            result = self.payment_service.create_payment(payment_data)
            
            return payments_pb2.PaymentResponse(
                payment_id=result.id,
                order_id=result.order_id,
                user_id=result.user_id,
                amount=result.amount,
                status=result.status.value,
                stripe_payment_intent_id=result.stripe_payment_intent_id or "",
                payment_method_token=result.payment_method_token,
                currency=result.currency,
                client_secret=""
            )
            
        except Exception as e:
            self.logger.error(f"gRPC CreatePayment failed: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return payments_pb2.PaymentResponse()
    
    def GetPayment(self, request, context):
        try:
            self.logger.info(f"gRPC GetPayment: {request.payment_id}")
            
            result = self.payment_service.get_payment(request.payment_id)
            
            return payments_pb2.PaymentResponse(
                payment_id=result.id,
                order_id=result.order_id,
                user_id=result.user_id,
                amount=result.amount,
                status=result.status.value,
                stripe_payment_intent_id=result.stripe_payment_intent_id or "",
                payment_method_token=result.payment_method_token,
                currency=result.currency,
                client_secret=""
            )
            
        except Exception as e:
            self.logger.error(f"gRPC GetPayment failed: {e}")
            if "not found" in str(e).lower():
                context.set_code(grpc.StatusCode.NOT_FOUND)
            else:
                context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return payments_pb2.PaymentResponse()
    
    def ProcessRefund(self, request, context):
        try:
            self.logger.info(f"gRPC ProcessRefund: {request.payment_id}")
            
            refund_data = pydantic_models.RefundRequest(
                amount=request.amount if request.amount > 0 else None,
                reason=request.reason or None
            )
            
            result = self.payment_service.create_refund(request.payment_id, refund_data)
            
            return payments_pb2.RefundResponse(
                refund_id=result["id"],
                status=result["status"],
                amount=result["amount"],
                currency=result["currency"],
                reason=result.get("reason", "")
            )
            
        except Exception as e:
            self.logger.error(f"gRPC ProcessRefund failed: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return payments_pb2.RefundResponse()


def serve_grpc(payment_service, host: str = "0.0.0.0", port: int = 50051):
    logger = logging.getLogger(__name__)
    
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    payments_pb2_grpc.add_PaymentServiceServicer_to_server(
        PaymentGRPCServer(payment_service, logger), server
    )
    
    server_address = f"{host}:{port}"
    server.add_insecure_port(server_address)
    
    logger.info(f"gRPC server started on {server_address}")
    server.start()
    server.wait_for_termination()