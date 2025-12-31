from database.database_models import OrderStatus

class PaymentStatusMapper:
    def __init__(self):
        self.mapping = {
            "succeeded": OrderStatus.PAID,
            "failed": OrderStatus.FAILED,
            "refunded": OrderStatus.REFUNDED,
            "canceled": OrderStatus.CANCELED
        }

    def map_payment_status(self, payment_status: str) -> OrderStatus:
        order_status = self.mapping.get(payment_status)
        if not order_status:
            raise ValueError(f"Unknown payment status: {payment_status}")
        return order_status