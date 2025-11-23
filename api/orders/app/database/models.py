from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List
from datetime import datetime
from enum import Enum

class OrderStatus(str, Enum):
    CREATED = "created"
    PAID = "paid"
    SHIPPED = "shipped"
    CANCELED = "canceled"

class OrderCreate(BaseModel):
    billing_address_id: Optional[str] = Field(None, description="Billing address ID")
    shipping_address_id: Optional[str] = Field(None, description="Shipping address ID")
    payment_method_token: Optional[str] = Field(None, description="Payment method token")

class OrderItemResponse(BaseModel):
    product_id: str
    name: str
    quantity: int
    unit_price: float

    model_config = ConfigDict(from_attributes=True)

class OrderResponse(BaseModel):
    id: str
    status: OrderStatus
    total: float
    items: List[OrderItemResponse]
    billing_address_id: Optional[str] = None
    shipping_address_id: Optional[str] = None
    created_at: str

    @field_validator('created_at', mode='before')
    @classmethod
    def convert_datetime(cls, v):
        if isinstance(v, datetime):
            return v.isoformat()
        return v
    
    model_config = ConfigDict(from_attributes=True)

class OrderList(BaseModel):
    items: List[OrderResponse]
    total: int
    page: int
    page_size: int

class OrderQueryParams(BaseModel):
    page: int = Field(1, ge=1, description="Page number must be positive")
    page_size: int = Field(20, ge=1, le=100, description="Page size must be between 1 and 100")

class ErrorResponse(BaseModel):
    type: str
    title: str
    status: int
    detail: str
    instance: Optional[str] = None
