from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List
from datetime import datetime


class CartItemRequest(BaseModel):
    product_id: str = Field(..., min_length=1, description="Product ID is required")
    quantity: int = Field(..., ge=1, description="Quantity must be at least 1")

    @field_validator('product_id')
    def product_id_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Product ID cannot be empty')
        return v.strip()


class CartItemUpdate(BaseModel):
    quantity: int = Field(..., ge=1, description="Quantity must be at least 1")


class CartItemResponse(BaseModel):
    id: str
    product_id: str
    name: str
    quantity: int
    unit_price: float

    model_config = ConfigDict(from_attributes=True)


class CartResponse(BaseModel):
    id: str
    user_id: str
    items: List[CartItemResponse]
    total: float


class CartList(BaseModel):
    items: List[CartResponse]
    total: int
    page: int
    page_size: int


class CartQueryParams(BaseModel):
    page: int = Field(1, ge=1, description="Page number must be positive")
    page_size: int = Field(20, ge=1, le=100, description="Page size must be between 1 and 100")


class ErrorResponse(BaseModel):
    type: str
    title: str
    status: int
    detail: str
    instance: Optional[str] = None
