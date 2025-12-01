from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List
from datetime import datetime


class ProductImageUpload(BaseModel):
    is_primary: bool = Field(False, description="Set as primary product image")


class ProductImage(BaseModel):
    id: str = Field(..., description="Image UUID")
    product_id: str = Field(..., description="Associated product ID")
    filename: str = Field(..., description="Server-generated filename")
    original_name: str = Field(..., description="Original client filename")
    mime_type: str = Field(..., description="Image MIME type", enum=["image/jpeg", "image/png", "image/webp"])
    size: int = Field(..., ge=1, description="File size in bytes")
    width: int = Field(..., ge=1, description="Image width in pixels")
    height: int = Field(..., ge=1, description="Image height in pixels")
    is_primary: bool = Field(..., description="Whether this is the primary product image")
    url: str = Field(..., description="Public URL to access the image")
    uploaded_at: datetime = Field(..., description="Upload timestamp")

    model_config = ConfigDict(from_attributes=True)


class ProductImageList(BaseModel):
    items: List[ProductImage]
    total: int


class PrimaryImageUpdate(BaseModel):
    image_id: str = Field(..., description="Image ID to set as primary")

class ProductRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Product name is required")
    price: float = Field(..., gt=0, description="Price must be greater than 0")
    stock: int = Field(..., ge=0, description="Stock cannot be negative")
    description: Optional[str] = Field(None, max_length=1000, description="Description cannot exceed 1000 characters")

    @field_validator('name')
    def name_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Product name cannot be empty')
        return v.strip()


class ProductPatch(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    price: Optional[float] = Field(None, gt=0)
    stock: Optional[int] = Field(None, ge=0)
    description: Optional[str] = Field(None, max_length=1000)

    @field_validator('*', mode='before')
    def empty_string_to_none(cls, v):
        if v == "":
            return None
        return v


class ProductResponse(BaseModel):
    id: str
    name: str
    price: float
    stock: int
    description: Optional[str]
    images: List['ProductImage'] = Field(default_factory=list)
    primary_image_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ProductList(BaseModel):
    items: List[ProductResponse]
    total: int
    page: int
    page_size: int


class InventoryUpdate(BaseModel):
    stock: int = Field(..., ge=0, description="Stock cannot be negative")


class ProductQueryParams(BaseModel):
    page: int = Field(1, ge=1, description="Page number must be positive")
    page_size: int = Field(20, ge=1, le=100, description="Page size must be between 1 and 100")
    q: Optional[str] = Field(None, description="Search query")


class InventoryResponse(BaseModel):
    id: str
    stock: int


class ErrorResponse(BaseModel):
    type: str
    title: str
    status: int
    detail: str
    instance: Optional[str] = None

