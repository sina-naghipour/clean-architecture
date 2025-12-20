import grpc
import orders_pb2
import orders_pb2_grpc
from optl.trace_decorator import trace_service_operation
from opentelemetry import trace

class OrdersGRPCClient:
    def __init__(self, host="orders-service", port=50051):
        self.channel = grpc.aio.insecure_channel(f"{host}:{port}")
        self.stub = orders_pb2_grpc.OrderServiceStub(self.channel)
        self.tracer = trace.get_tracer(__name__)
    
    @trace_service_operation("update_order_payment_status")
    async def update_order_payment_status(
        self, 
        order_id: str, 
        payment_id: str, 
        status: str,
        stripe_payment_intent_id: str = ""
    ):
        try:
            with self.tracer.start_as_current_span("grpc.UpdateOrderPaymentStatus") as span:
                span.set_attributes({
                    "grpc.service": "OrderService",
                    "grpc.method": "UpdateOrderPaymentStatus",
                    "order.id": order_id,
                    "payment.id": payment_id,
                    "payment.status": status,
                    "stripe.id": stripe_payment_intent_id
                })
                
                request = orders_pb2.UpdateOrderPaymentRequest(
                    order_id=order_id,
                    payment_id=payment_id,
                    status=status,
                    stripe_payment_intent_id=stripe_payment_intent_id
                )
                
                response = await self.stub.UpdateOrderPaymentStatus(request)
                span.set_attribute("grpc.success", True)
                return response.success
        except grpc.RpcError as e:
            span = trace.get_current_span()
            span.set_attribute("grpc.error_code", e.code().name)
            span.set_attribute("grpc.error_details", e.details()[:100])
            span.set_attribute("grpc.success", False)
            print(f"Failed to notify Orders: {e.code().name} - {e.details()}")
            return False
    
    async def close(self):
        await self.channel.close()