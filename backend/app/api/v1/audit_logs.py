"""Security Audit Log Inspection and Compliance Export Endpoints for InferX."""

import csv
import io
import json
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

try:
    from backend.app.api.deps import AuthContext, get_optional_auth_context, require_role
    from backend.app.api.v1.schemas import APIResponse
    from backend.app.core.logging import get_correlation_id
    from backend.app.core.security import has_sufficient_role
    from backend.app.db.session import get_db
    from backend.app.repositories.audit_log_repository import audit_log_repository
    from backend.app.schemas.audit_log import AuditLogListResponse, AuditLogResponse
except (ImportError, ModuleNotFoundError):
    from app.api.deps import AuthContext, get_optional_auth_context, require_role
    from app.api.v1.schemas import APIResponse
    from app.core.logging import get_correlation_id
    from app.core.security import has_sufficient_role
    from app.db.session import get_db
    from app.repositories.audit_log_repository import audit_log_repository
    from app.schemas.audit_log import AuditLogListResponse, AuditLogResponse

router = APIRouter()


@router.get("", response_model=APIResponse[AuditLogListResponse])
async def list_audit_logs(
    action: Optional[str] = Query(None, description="Filter by event action"),
    resource_type: Optional[str] = Query(None, description="Filter by target resource"),
    actor_id: Optional[str] = Query(None, description="Filter by actor ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    auth: Optional[AuthContext] = Depends(get_optional_auth_context),
) -> APIResponse[AuditLogListResponse]:
    """Retrieve security audit trails (strictly requires admin role if authenticated)."""
    if auth and not has_sufficient_role(auth.role, "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: requires 'admin' role",
        )

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


@router.get("/export")
async def export_audit_logs(
    export_format: Literal["csv", "json"] = Query(default="csv", alias="format", description="Export file format"),
    action: Optional[str] = Query(None, description="Filter by event action"),
    resource_type: Optional[str] = Query(None, description="Filter by target resource"),
    actor_id: Optional[str] = Query(None, description="Filter by actor ID"),
    limit: int = Query(1000, ge=1, le=5000),
    db: AsyncSession = Depends(get_db),
    auth: Optional[AuthContext] = Depends(get_optional_auth_context),
) -> Response:
    """Export compliance audit trails in streaming CSV or JSON format."""
    if auth and not has_sufficient_role(auth.role, "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: requires 'admin' role",
        )

    logs = await audit_log_repository.list_logs(
        db=db,
        action=action,
        resource_type=resource_type,
        actor_id=actor_id,
        skip=0,
        limit=limit,
    )

    if export_format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "created_at", "action", "actor_id", "resource_type", "resource_id", "status", "ip_address", "details"])

        for log in logs:
            writer.writerow([
                log.id,
                log.created_at.isoformat() if log.created_at else "",
                log.action,
                log.actor_id or "",
                log.resource_type,
                log.resource_id or "",
                log.status,
                log.ip_address or "",
                json.dumps(log.details or {}),
            ])

        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=inferx-audit-logs.csv"},
        )

    # JSON export
    serialized = [AuditLogResponse.model_validate(l).model_dump(mode="json") for l in logs]
    json_bytes = json.dumps(serialized, indent=2).encode("utf-8")
    return StreamingResponse(
        iter([json_bytes.decode("utf-8")]),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=inferx-audit-logs.json"},
    )
