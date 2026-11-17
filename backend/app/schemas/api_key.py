"""Pydantic Schemas for API Key Management."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ApiKeyCreate(BaseModel):
    """Payload schema for generating an API key."""

    name: str = Field(..., min_length=1, max_length=128, description="Descriptive identifier for the API key")
    role: str = Field(default="operator", description="RBAC role assigned to the key: admin, operator, viewer")
    rate_limit_rps: int = Field(default=50, ge=1, le=10000, description="Rate limit allowance in requests per second")
    expires_at: Optional[datetime] = Field(default=None, description="Optional ISO timestamp expiration date")


class ApiKeyResponse(BaseModel):
    """Safe response schema for an API key record (does not reveal secret key)."""

    id: str
    name: str
    prefix: str
    role: str
    is_active: bool
    rate_limit_rps: int
    expires_at: Optional[datetime] = None
    user_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ApiKeyCreatedResponse(ApiKeyResponse):
    """Returned once upon key creation, revealing the plaintext raw key."""

    raw_key: str = Field(..., description="Plaintext raw API key. Revealed only once.")


class ApiKeyListResponse(BaseModel):
    """Paginated response for API keys."""

    items: List[ApiKeyResponse]
    total: int
    skip: int
    limit: int
