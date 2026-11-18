"""Token Quota and Enterprise Governance Pydantic Schemas."""

from datetime import datetime
from typing import List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field


class QuotaPolicyBase(BaseModel):
    """Base fields for quota limits and rate constraints."""
    name: str = Field(min_length=3, max_length=128, description="Unique human-readable quota policy name")
    target_type: Literal["user", "api_key", "tenant"] = Field(
        default="user", description="Subject type governed by this quota"
    )
    target_id: Optional[str] = Field(
        default=None, description="Optional target user ID, API key ID, or tenant ID"
    )
    max_tokens_per_day: int = Field(default=1_000_000, ge=1_000, description="Daily token cap")
    max_tokens_per_month: int = Field(default=30_000_000, ge=10_000, description="Monthly token cap")
    rate_limit_rpm: int = Field(default=120, ge=1, le=10000, description="Max requests per minute")
    is_active: bool = Field(default=True, description="Whether policy is enforced")


class QuotaPolicyCreate(QuotaPolicyBase):
    """Payload to create a new quota policy."""
    pass


class QuotaPolicyUpdate(BaseModel):
    """Payload to update an existing quota policy."""
    name: Optional[str] = Field(default=None, min_length=3, max_length=128)
    max_tokens_per_day: Optional[int] = Field(default=None, ge=1_000)
    max_tokens_per_month: Optional[int] = Field(default=None, ge=10_000)
    rate_limit_rpm: Optional[int] = Field(default=None, ge=1, le=10000)
    is_active: Optional[bool] = None


class QuotaPolicyResponse(QuotaPolicyBase):
    """Response schema for a single quota policy with live consumption."""
    id: str
    used_tokens_today: int
    used_tokens_this_month: int
    total_requests_count: int
    last_reset_at: datetime
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class QuotaUsageSummary(BaseModel):
    """Summary of token budget remaining and consumption percentages."""
    policy_id: str
    policy_name: str
    target_type: str
    target_id: Optional[str] = None
    daily_quota: int
    daily_used: int
    daily_remaining: int
    daily_usage_pct: float
    monthly_quota: int
    monthly_used: int
    monthly_remaining: int
    monthly_usage_pct: float
    rate_limit_rpm: int
    is_exhausted: bool


class QuotaListResponse(BaseModel):
    """Paginated list of quota policies."""
    items: List[QuotaPolicyResponse]
    total: int
