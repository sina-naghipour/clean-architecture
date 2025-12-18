from .order_helpers import create_problem_response
from fastapi import Request
from fastapi.responses import JSONResponse
from database import pydantic_models
from datetime import datetime
from uuid import UUID
from repositories.orders_repository import OrderRepository
from database.database_models import OrderDB, OrderStatus
from decorators.order_services_decorators import OrderServiceDecorators
from protos import payments_pb2, payments_pb2_grpc

import grpc.aio
import os

class PaymentGRPCClient:
    def __init__(self):
        self.host = os.getenv("PAYMENTS_GRPC_HOST", "payments")
        self.port = int(os.getenv("PAYMENTS_GRPC_PORT", "50051"))
        self.channel = None
    
    async def connect(self):
        if not self.channel:
            server_address = f"{self.host}:{self.port}"
            self.channel = grpc.aio.insecure_channel(server_address)
    
    async def create_payment(self, order_id, amount, user_id, payment_method_token):
        await self.connect()
        
        stub = payments_pb2_grpc.PaymentServiceStub(self.channel)
        
        request = payments_pb2.CreatePaymentRequest(
            order_id=order_id,
            user_id=user_id,
            amount=amount,
            payment_method_token=payment_method_token,
            currency="usd"
        )
        
        response = await stub.CreatePayment(request)
        return response.payment_id
    
    async def get_payment(self, payment_id):
        await self.connect()
        
        stub = payments_pb2_grpc.PaymentServiceStub(self.channel)
        request = payments_pb2.GetPaymentRequest(payment_id=payment_id)
        
        response = await stub.GetPayment(request)
        return {
            "id": response.payment_id,
            "status": response.status,
            "client_secret": response.client_secret
        }
    
    async def close(self):
        if self.channel:
            await self.channel.close()