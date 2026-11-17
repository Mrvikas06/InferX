"""Security Audit Log Inspection Endpoints for InferX."""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import require_role
from backend.app.api.v1.schemas import APIResponse
from backend.app.core.logging import get_correlation_id
from backend.app.db.session import get_db
from backend.app.repositories.audit_log_repository import audit_log_repository
from backend.app.schemas.audit_log import (
    AuditLogListResponse,
    AuditLogResponse,
)

router = APIRouter()


@router.get(
    "",
    response_model=APIResponse[AuditLogListResponse],
    dependencies=[Depends(require_role("admin"))],
)
async def list_audit_logs(
    action: Optional[str] = Query(None, description="Filter by event action"),
    resource_type: Optional[str] = Query(None, description="Filter by target resource"),
    actor_id: Optional[str] = Query(None, description="Filter by actor ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[AuditLogListResponse]:
    """Retrieve security audit trails (restricted strictly to Admin role)."""
    items = await audit_log_repository.list_logs(
        db=db,
        action=action,
        resource_type=resource_type,
        actor_id=actor_id,
        skip=skip,
        limit=limit,
    )
    total = await audit_log_repository.count_logs(
        db=db,
        action=action,
        resource_type=resource_type,
        actor_id=actor_id,
    )

    return APIResponse[AuditLogListResponse](
        success=True,
        data=AuditLogListResponse(
            items=[AuditLogResponse.model_validate(log) for log in items],
            total=total,
            skip=skip,
            limit=limit,
        ),
        correlation_id=get_correlation_id(),
    )
