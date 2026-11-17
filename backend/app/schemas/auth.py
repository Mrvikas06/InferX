"""Pydantic Schemas for Authentication and User Management."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserRegister(BaseModel):
    """Payload schema for user account registration."""

    email: str = Field(..., min_length=5, max_length=255, description="Valid email address")
    password: str = Field(..., min_length=8, max_length=128, description="Plaintext password (min 8 chars)")
    full_name: Optional[str] = Field(default=None, max_length=128, description="User full display name")
    role: str = Field(default="viewer", description="Role: admin, operator, viewer")


class UserLogin(BaseModel):
    """Payload schema for credential login."""

    email: str = Field(..., min_length=5, max_length=255)
    password: str = Field(..., min_length=1, max_length=128)


class TokenResponse(BaseModel):
    """JWT Token pair response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Access token expiration window in seconds")


class TokenRefresh(BaseModel):
    """Payload schema for token refresh rotation."""

    refresh_token: str = Field(..., min_length=1, description="Valid refresh token")


class UserResponse(BaseModel):
    """Response schema for user account entity."""

    id: str
    email: str
    full_name: Optional[str] = None
    role: str
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    """Payload schema for user modification."""

    full_name: Optional[str] = Field(default=None, max_length=128)
    role: Optional[str] = Field(default=None, description="Role: admin, operator, viewer")
    is_active: Optional[bool] = None
    password: Optional[str] = Field(default=None, min_length=8, max_length=128)
