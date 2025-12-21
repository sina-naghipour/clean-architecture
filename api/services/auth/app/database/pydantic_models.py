from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from typing import Optional
from datetime import datetime


class User(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters long")
    name: str = Field(..., min_length=1, description="Name is required")

    @field_validator('password')
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        if len(v) > 128:
            raise ValueError('Password must be less than 128 characters')
        
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        if not any(c in special_chars for c in v):
            raise ValueError('Password must contain at least one special character')
        
        weak_passwords = {'password', '12345678', 'qwertyui', 'admin123', 'letmein'}
        if v.lower() in weak_passwords:
            raise ValueError('Password is too common, please choose a stronger one')
        
        for i in range(len(v) - 2):
            if v[i:i+3].isalpha() and ord(v[i+1]) == ord(v[i]) + 1 and ord(v[i+2]) == ord(v[i]) + 2:
                raise ValueError('Password contains sequential characters')
        
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1, description="Password is required")


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., alias="refreshToken", description="Refresh token is required")


class PasswordChangeRequest(BaseModel):
    old_password: str = Field(..., alias="oldPassword", description="Old password is required")
    new_password: str = Field(..., alias="newPassword", min_length=8, description="New password must be at least 8 characters long")

class UserResponse(BaseModel):
    id: str
    email: EmailStr
    name: str

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str = Field(..., alias="accessToken")
    refresh_token: str = Field(..., alias="refreshToken")


class AccessTokenResponse(BaseModel):
    access_token: str = Field(..., alias="accessToken")


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str


class UserInDB(BaseModel):
    id: str
    email: EmailStr
    password: str
    name: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenPayload(BaseModel):
    user_id: str
    email: EmailStr
    name: str


class ErrorResponse(BaseModel):
    type: str
    title: str
    status: int
    detail: str
    instance: Optional[str] = None