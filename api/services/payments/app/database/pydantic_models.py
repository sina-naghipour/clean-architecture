from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum

class PaymentStatus(str, Enum):
    CREATED = "created"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELED = "canceled"

class PaymentCreate(BaseModel):
    order_id: str = Field(...)
    amount: float = Field(..., gt=0)
    user_id: str = Field(...)
    payment_method_token: str = Field(...)
    currency: str = Field(default="usd")
    metadata: Optional[Dict[str, Any]] = Field(default=None)

class PaymentResponse(BaseModel):
    id: str
    order_id: str
    user_id: str
    amount: float
    status: PaymentStatus
    stripe_payment_intent_id: Optional[str] = None
    payment_method_token: str
    currency: str
    metadata: Optional[Dict[str, Any]] = None
    created_at: str
    updated_at: str

    @field_validator('created_at', 'updated_at', mode='before')
    @classmethod
    def convert_datetime(cls, v):
        if isinstance(v, datetime):
            return v.isoformat()
        return v
    
    model_config = ConfigDict(from_attributes=True)

class PaymentUpdate(BaseModel):
    status: Optional[PaymentStatus] = None
    stripe_payment_intent_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class RefundRequest(BaseModel):
    amount: Optional[float] = Field(None, gt=0)
    reason: Optional[str] = None

class WebhookEvent(BaseModel):
    id: str
    type: str
    data: Dict[str, Any]
    created: int

class ErrorResponse(BaseModel):
    type: str
    title: str
    status: int
    detail: str
    instance: Optional[str] = None