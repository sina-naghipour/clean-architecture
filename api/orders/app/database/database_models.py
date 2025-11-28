from sqlalchemy import Column, String, Float, DateTime, Enum as SQLEnum, JSON
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
from enum import Enum
from typing import Dict, Any, List

from .connection import Base

class OrderStatus(str, Enum):
    CREATED = "created"
    PAID = "paid"
    SHIPPED = "shipped"
    CANCELED = "canceled"

class OrderDB(Base):
    __tablename__ = "orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    status = Column(SQLEnum(OrderStatus), nullable=False, default=OrderStatus.CREATED)
    total = Column(Float, nullable=False)
    billing_address_id = Column(String, nullable=True)
    shipping_address_id = Column(String, nullable=True)
    payment_method_token = Column(String, nullable=True)
    items = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "status": self.status.value,
            "total": self.total,
            "billing_address_id": self.billing_address_id,
            "shipping_address_id": self.shipping_address_id,
            "items": self.items,
            "created_at": self.created_at
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
            items=data["items"],
            created_at=data.get("created_at", datetime.utcnow())
        )