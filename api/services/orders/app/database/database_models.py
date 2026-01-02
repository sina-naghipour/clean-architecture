from sqlalchemy import Column, String, Float, DateTime, Enum as SQLEnum, JSON
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
from enum import Enum
from typing import Dict, Any

from .connection import Base

class OrderStatus(str, Enum):
    CREATED = "created"
    PAID = "paid"
    SHIPPED = "shipped"
    CANCELED = "canceled"
    PENDING = "pending"
    FAILED = "failed"
    REFUNDED = "refunded"

class OrderDB(Base):
    __tablename__ = "orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    status = Column(SQLEnum(OrderStatus), nullable=False, default=OrderStatus.CREATED)
    total = Column(Float, nullable=False)
    billing_address_id = Column(String, nullable=True)
    shipping_address_id = Column(String, nullable=True)
    payment_method_token = Column(String, nullable=True)
    payment_id = Column(String, nullable=True)
    items = Column(JSON, nullable=False)
    user_id = Column(String, nullable=True)
    receipt_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    checkout_url = Column(String, nullable=True)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "status": self.status.value,
            "total": self.total,
            "billing_address_id": self.billing_address_id,
            "shipping_address_id": self.shipping_address_id,
            "payment_method_token": self.payment_method_token,
            "payment_id": self.payment_id,
            "items": self.items,
            "created_at": self.created_at,
            "user_id": self.user_id,
            "checkout_url": self.checkout_url,
            "receipt_url": self.receipt_url,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OrderDB':
        return cls(
            id=uuid.UUID(data["id"]) if "id" in data else uuid.uuid4(),
            status=data["status"],
            total=data["total"],
            billing_address_id=data.get("billing_address_id"),
            shipping_address_id=data.get("shipping_address_id"),
            payment_method_token=data.get("payment_method_token"),
            payment_id=data.get("payment_id"),
            items=data["items"],
            created_at=data.get("created_at", datetime.utcnow()),
            user_id=data.get("user_id"),
            receipt_url=data.get("receipt_url"),
            checkout_url=data.get("checkout_url"),
        )