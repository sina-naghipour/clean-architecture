import httpx
import os
from typing import Optional

class NotificationService:
    def __init__(self, http_client: Optional[httpx.AsyncClient] = None):
        self.http_client = http_client
        self.orders_webhook_url = os.getenv("ORDERS_WEBHOOK_URL", "http://orders:8002/webhooks/payment-updates")
        self.internal_api_key = os.getenv("INTERNAL_API_KEY", "default_internal_key")
    
    async def send_notification(self, data: dict, idempotency_key: str) -> bool:
        client = self.http_client or httpx.AsyncClient()
        use_context_manager = self.http_client is None
        
        if use_context_manager:
            async with client as http_client:
                response = await http_client.post(
                    self.orders_webhook_url,
                    json=data,
                    headers={
                        "X-API-Key": self.internal_api_key,
                        "X-Idempotency-Key": idempotency_key
                    },
                    timeout=5.0
                )
        else:
            response = await client.post(
                self.orders_webhook_url,
                json=data,
                headers={
                    "X-API-Key": self.internal_api_key,
                    "X-Idempotency-Key": idempotency_key
                },
                timeout=5.0
            )
        
        return response.status_code == 200