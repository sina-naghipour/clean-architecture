from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List
from datetime import datetime
from enum import Enum

class OrderStatus(str, Enum):
    CREATED = "created"
    PAID = "paid"
    SHIPPED = "shipped"
    PENDING = "pending"
    CANCELED = "canceled"
    FAILED = "failed"
    
class OrderItemCreate(BaseModel):
    product_id: str = Field(...)
    name: str = Field(...)
    quantity: int = Field(..., ge=1)
    unit_price: float = Field(..., ge=0)

class OrderCreate(BaseModel):
    items: List[OrderItemCreate] = Field(...)
    billing_address_id: str = Field(...)
    shipping_address_id: str = Field(...)
    payment_method_token: str = Field(...)

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
    payment_id: Optional[str] = None
    client_secret: Optional[str] = None
    receipt_url: Optional[str] = None
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
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)

class ErrorResponse(BaseModel):
    type: str
    title: str
    status: int
    detail: str
    instance: Optional[str] = None