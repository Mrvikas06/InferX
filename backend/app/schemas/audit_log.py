"""Pydantic Schemas for Security Audit Logs."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class AuditLogResponse(BaseModel):
    """Response schema for audit log entries."""

    id: str
    action: str
    actor_id: Optional[str] = None
    resource_type: str
    resource_id: Optional[str] = None
    status: str
    details: Dict[str, Any] = Field(default_factory=dict)
    ip_address: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AuditLogListResponse(BaseModel):
    """Paginated response for audit log entries."""

    items: List[AuditLogResponse]
    total: int
    skip: int
    limit: int
