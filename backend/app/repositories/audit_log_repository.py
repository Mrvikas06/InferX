"""Audit Log Repository for Security and Compliance Tracking."""

from typing import Any, Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

try:
    from backend.app.models.audit_log import AuditLog
    from backend.app.repositories.base import BaseRepository
    from backend.app.schemas.audit_log import AuditLogResponse
except (ImportError, ModuleNotFoundError):
    from app.models.audit_log import AuditLog
    from app.repositories.base import BaseRepository
    from app.schemas.audit_log import AuditLogResponse


class AuditLogRepository(BaseRepository[AuditLog, AuditLogResponse, AuditLogResponse]):
    """Data access repository for AuditLog records."""

    async def record(
        self,
        db: AsyncSession,
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        actor_id: Optional[str] = None,
        status: str = "success",
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
    ) -> AuditLog:
        """Create and persist an audit event entry."""
        log_entry = AuditLog(
            action=action,
            actor_id=actor_id,
            resource_type=resource_type,
            resource_id=resource_id,
            status=status,
            details=details or {},
            ip_address=ip_address,
        )
        db.add(log_entry)
        await db.flush()
        await db.refresh(log_entry)
        return log_entry

    async def list_logs(
        self,
        db: AsyncSession,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        actor_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[AuditLog]:
        """Query audit log events with filtering."""
        stmt = select(AuditLog)
        if action:
            stmt = stmt.where(AuditLog.action == action)
        if resource_type:
            stmt = stmt.where(AuditLog.resource_type == resource_type)
        if actor_id:
            stmt = stmt.where(AuditLog.actor_id == actor_id)

        stmt = stmt.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def count_logs(
        self,
        db: AsyncSession,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        actor_id: Optional[str] = None,
    ) -> int:
        """Count audit log entries."""
        stmt = select(func.count(AuditLog.id))
        if action:
            stmt = stmt.where(AuditLog.action == action)
        if resource_type:
            stmt = stmt.where(AuditLog.resource_type == resource_type)
        if actor_id:
            stmt = stmt.where(AuditLog.actor_id == actor_id)

        result = await db.execute(stmt)
        return result.scalar() or 0


audit_log_repository = AuditLogRepository(AuditLog)
