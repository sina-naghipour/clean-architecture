from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List
from datetime import datetime


class ProductRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Product name is required")
    price: float = Field(..., gt=0, description="Price must be greater than 0")
    stock: int = Field(..., ge=0, description="Stock cannot be negative")
    description: Optional[str] = Field(None, max_length=1000, description="Description cannot exceed 1000 characters")
    tags: List[str] = Field(default_factory=list, description="List of product tags")
    images: List[str] = Field(default_factory=list, description="List of image URLs/paths")

    @field_validator('name')
    def name_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Product name cannot be empty')
        return v.strip()

    @field_validator('tags')
    def validate_tags(cls, v):
        if v is None:
            return []
        unique_tags = list(set(tag.strip() for tag in v if tag and tag.strip()))
        return unique_tags

    @field_validator('images')
    def validate_images(cls, v):
        if v is None:
            return []
        validated_images = []
        for img in v:
            if img and img.strip():
                validated_images.append(img.strip())
        return validated_images


class ProductPatch(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    price: Optional[float] = Field(None, gt=0)
    stock: Optional[int] = Field(None, ge=0)
    description: Optional[str] = Field(None, max_length=1000)
    tags: Optional[List[str]] = Field(None, description="List of product tags")
    images: Optional[List[str]] = Field(None, description="List of image URLs/paths")

    @field_validator('*', mode='before')
    def empty_string_to_none(cls, v):
        if v == "":
            return None
        return v

    @field_validator('tags', mode='before')
    def normalize_tags(cls, v):
        if v == []:
            return None
        return v

    @field_validator('images', mode='before')
    def normalize_images(cls, v):
        if v == []:
            return None
        return v


class ProductResponse(BaseModel):
    id: str
    name: str
    price: float
    stock: int
    description: Optional[str]
    tags: List[str]
    images: List[str]
    created_at: datetime
    updated_at: datetime

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
    tags: Optional[List[str]] = Field(None, description="Filter by tags")
    min_price: Optional[float] = Field(None, ge=0, description="Minimum price filter")
    max_price: Optional[float] = Field(None, ge=0, description="Maximum price filter")


class InventoryResponse(BaseModel):
    id: str
    stock: int


class ProductTagUpdate(BaseModel):
    tags: List[str] = Field(..., description="New list of tags for the product")

    @field_validator('tags')
    def validate_tags(cls, v):
        if not v:
            raise ValueError('Tags list cannot be empty')
        unique_tags = list(set(tag.strip() for tag in v if tag and tag.strip()))
        if not unique_tags:
            raise ValueError('Tags list cannot contain only empty strings')
        return unique_tags


class ProductImageUpdate(BaseModel):
    images: List[str] = Field(..., description="New list of image URLs for the product")

    @field_validator('images')
    def validate_images(cls, v):
        if not v:
            raise ValueError('Images list cannot be empty')
        validated_images = [img.strip() for img in v if img and img.strip()]
        if not validated_images:
            raise ValueError('Images list cannot contain only empty strings')
        return validated_images


class ProductImageAdd(BaseModel):
    image_url: str = Field(..., description="Image URL to add to product")
    
    @field_validator('image_url')
    def validate_image_url(cls, v):
        if not v or not v.strip():
            raise ValueError('Image URL cannot be empty')
        return v.strip()


class ErrorResponse(BaseModel):
    type: str
    title: str
    status: int
    detail: str
    instance: Optional[str] = None