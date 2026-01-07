import grpc
import asyncio
from typing import Optional, Dict, Any
import logging
from protos import commissions_pb2, commissions_pb2_grpc

class PaymentGRPCClient:
    def __init__(self, logger: logging.Logger, host: str = "payments-service", port: int = 50051):
        self.logger = logger
        self.host = host
        self.port = port
        self._circuit_open = False
        self._failure_count = 0
    
    async def get_commission_report(self, referrer_id: str) -> Dict[str, Any]:
        if self._circuit_open:
            self.logger.warning("Circuit breaker open - commission service unavailable")
            return self._get_empty_report(referrer_id)
        
        max_retries = 3
        base_delay = 1
        
        for attempt in range(max_retries):
            try:
                async with grpc.aio.insecure_channel(f'{self.host}:{self.port}') as channel:
                    stub = commissions_pb2_grpc.CommissionServiceStub(channel)
                    
                    response = await stub.GetCommissionReport(
                        commissions_pb2.CommissionRequest(referrer_id=referrer_id),
                        timeout=10,
                        metadata=(('service-name', 'auth-service'),)
                    )
                    
                    self._failure_count = 0
                    self._circuit_open = False
                    
                    return {
                        'referrer_id': response.referrer_id,
                        'total_commissions': response.total_commissions,
                        'total_amount': response.total_amount,
                        'pending_amount': response.pending_amount,
                        'paid_amount': response.paid_amount,
                        'commissions': [
                            {
                                'id': c.id,
                                'order_id': c.order_id,
                                'amount': c.amount,
                                'status': c.status,
                                'created_at': c.created_at
                            } for c in response.commissions
                        ]
                    }
                    
            except grpc.RpcError as e:
                self._failure_count += 1
                self.logger.warning(f"Commission gRPC attempt {attempt + 1} failed: {e.code()} - {e.details()}")
                
                if self._failure_count >= 5:
                    self._circuit_open = True
                    self.logger.error("Circuit breaker opened for commission service")
                
                if attempt == max_retries - 1:
                    self.logger.error(f"All {max_retries} attempts failed for commission report")
                    return self._get_empty_report(referrer_id)
                
                await asyncio.sleep(base_delay * (2 ** attempt))
            
            except Exception as e:
                self._failure_count += 1
                self.logger.error(f"Unexpected error in commission gRPC: {str(e)}")
                
                if self._failure_count >= 5:
                    self._circuit_open = True
                
                if attempt == max_retries - 1:
                    return self._get_empty_report(referrer_id)
                
                await asyncio.sleep(base_delay * (2 ** attempt))
        
        return self._get_empty_report(referrer_id)
    
    def _get_empty_report(self, referrer_id: str) -> Dict[str, Any]:
        return {
            'referrer_id': referrer_id,
            'total_commissions': 0,
            'total_amount': 0.0,
            'pending_amount': 0.0,
            'paid_amount': 0.0,
            'commissions': [],
            'service_unavailable': True
        }
