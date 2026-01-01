"""
Authentication related Pydantic schemas
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class LoginRequest(BaseModel):
    """Login request schema"""
    email: EmailStr
    password: str = Field(min_length=6, description="User password")


class Token(BaseModel):
    """Token response schema"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenPayload(BaseModel):
    """Token payload schema"""
    sub: str  # User ID
    email: str
    exp: int  # Expiration timestamp


class UserCreate(BaseModel):
    """User creation schema"""
    email: EmailStr
    password: str = Field(min_length=6, description="User password")
    is_active: bool = True


class UserResponse(BaseModel):
    """User response schema"""
    id: str
    email: str
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True