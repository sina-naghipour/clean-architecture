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


class ProductImageBatchUpload(BaseModel):
    make_primary_first: bool = Field(False, description="Make first uploaded image primary")

class ProductImageBatchResponse(BaseModel):
    success: List[ProductImage] = Field(..., description="Successfully uploaded images")
    failed: List[dict] = Field(default_factory=list, description="Failed uploads with reasons")
    total: int = Field(..., description="Total files attempted")
    successful_count: int = Field(..., description="Number of successful uploads")
