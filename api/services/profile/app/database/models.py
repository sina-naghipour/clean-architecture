from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from enum import Enum

class ProfileUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone: Optional[str] = Field(None, min_length=10, max_length=20)

class PasswordChange(BaseModel):
    old_password: str = Field(..., min_length=8, description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")

class AddressRequest(BaseModel):
    line: str = Field(..., min_length=1, max_length=200, description="Street address")
    city: str = Field(..., min_length=1, max_length=100, description="City")
    postal_code: str = Field(..., min_length=1, max_length=20, description="Postal code")
    country: str = Field(..., min_length=1, max_length=100, description="Country")

class AddressResponse(BaseModel):
    id: str
    line: str
    city: str
    postal_code: str
    country: str

    model_config = ConfigDict(from_attributes=True)

class UserResponse(BaseModel):
    id: str
    email: str
    name: str

    model_config = ConfigDict(from_attributes=True)

class ErrorResponse(BaseModel):
    type: str
    title: str
    status: int
    detail: str
    instance: Optional[str] = None
