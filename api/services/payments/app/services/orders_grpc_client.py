import grpc
import orders_pb2
import orders_pb2_grpc

class OrdersGRPCClient:
    def __init__(self, host="orders-service", port=50051):
        self.channel = grpc.aio.insecure_channel(f"{host}:{port}")
        self.stub = orders_pb2_grpc.OrderServiceStub(self.channel)
    
    async def update_order_payment_status(
        self, 
        order_id: str, 
        payment_id: str, 
        status: str,
        stripe_payment_intent_id: str = ""
    ):
        try:
            request = orders_pb2.UpdateOrderPaymentRequest(
                order_id=order_id,
                payment_id=payment_id,
                status=status,
                stripe_payment_intent_id=stripe_payment_intent_id
            )
            
            response = await self.stub.UpdateOrderPaymentStatus(request)
            return response.success
        except grpc.RpcError as e:
            print(f"Failed to notify Orders: {e.code().name} - {e.details()}")
            return False
    
    async def close(self):
        await self.channel.close()