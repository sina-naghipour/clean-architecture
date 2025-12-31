from datetime import datetime
from database import pydantic_models
from database.database_models import OrderDB

class OrderResponseBuilder:
    @staticmethod
    def build_response(order_db: OrderDB) -> pydantic_models.OrderResponse:
        order_items = [
            pydantic_models.OrderItemResponse(
                product_id=item['product_id'],
                name=item['name'],
                quantity=item['quantity'],
                unit_price=item['unit_price'],
            ) for item in order_db.items
        ]

        return pydantic_models.OrderResponse(
            id=str(order_db.id),
            status=order_db.status,
            total=order_db.total,
            items=order_items,
            billing_address_id=order_db.billing_address_id,
            shipping_address_id=order_db.shipping_address_id,
            payment_id=order_db.payment_id,
            created_at=order_db.created_at.isoformat() if order_db.created_at else datetime.utcnow().isoformat(),
            receipt_url=order_db.receipt_url,
            client_secret=getattr(order_db, 'client_secret', None)
        )