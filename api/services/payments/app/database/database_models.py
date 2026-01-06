from sqlalchemy import Column, String, Float, DateTime, Enum as SQLEnum, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
import uuid
from enum import Enum
from typing import Dict, Any

from .connection import Base

class PaymentStatus(str, Enum):
    CREATED = "created"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELED = "canceled"

class PaymentDB(Base):
    __tablename__ = "payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(String, nullable=False)
    user_id = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    status = Column(SQLEnum(PaymentStatus), nullable=False, default=PaymentStatus.CREATED)
    stripe_payment_intent_id = Column(String, nullable=True)
    payment_method_token = Column(String, nullable=False)
    currency = Column(String, nullable=False, default="usd")
    client_secret = Column(String, nullable=True, default="PENDING") 
    checkout_session_id = Column(String, nullable=True)
    checkout_url = Column(String, nullable=True)
    referrer_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "order_id": self.order_id,
            "user_id": self.user_id,
            "amount": self.amount,
            "status": self.status.value,
            "stripe_payment_intent_id": self.stripe_payment_intent_id,
            "payment_method_token": self.payment_method_token,
            "currency": self.currency,
            "referrer_id": self.referrer_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PaymentDB':
        return cls(
            id=uuid.UUID(data["id"]) if "id" in data else uuid.uuid4(),
            order_id=data["order_id"],
            user_id=data["user_id"],
            amount=data["amount"],
            status=data.get("status", PaymentStatus.CREATED),
            stripe_payment_intent_id=data.get("stripe_payment_intent_id"),
            payment_method_token=data["payment_method_token"],
            currency=data.get("currency", "usd"),
            referrer_id=data.get("referrer_id"),
            created_at=data.get("created_at", datetime.utcnow()),
            updated_at=data.get("updated_at", datetime.utcnow())
        )


class CommissionDB(Base):
    __tablename__ = "commissions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    referrer_id = Column(String, nullable=False)
    order_id = Column(String, unique=True, nullable=False)
    amount = Column(Float, nullable=False)
    status = Column(String, nullable=False, default='pending')
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    audit_log = Column(JSONB, default=dict)