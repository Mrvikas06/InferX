"""Enterprise Governance, Token Quota Policies, and Tenant Limits API."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

try:
    from backend.app.api.deps import AuthContext, get_optional_auth_context
    from backend.app.api.v1.schemas import APIResponse
    from backend.app.core.logging import get_correlation_id
    from backend.app.core.security import has_sufficient_role
    from backend.app.db.session import get_db
    from backend.app.repositories.quota_repository import quota_repository
    from backend.app.schemas.quota import (
        QuotaListResponse,
        QuotaPolicyCreate,
        QuotaPolicyResponse,
        QuotaPolicyUpdate,
        QuotaUsageSummary,
    )
except (ImportError, ModuleNotFoundError):
    from app.api.deps import AuthContext, get_optional_auth_context
    from app.api.v1.schemas import APIResponse
    from app.core.logging import get_correlation_id
    from app.core.security import has_sufficient_role
    from app.db.session import get_db
    from app.repositories.quota_repository import quota_repository
    from app.schemas.quota import (
        QuotaListResponse,
        QuotaPolicyCreate,
        QuotaPolicyResponse,
        QuotaPolicyUpdate,
        QuotaUsageSummary,
    )

router = APIRouter(prefix="/governance", tags=["Enterprise Governance & Quotas"])


@router.get("/quotas", response_model=APIResponse[QuotaListResponse])
async def list_quota_policies(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    auth: Optional[AuthContext] = Depends(get_optional_auth_context),
) -> APIResponse[QuotaListResponse]:
    """List all configured token quota policies."""
    items = await quota_repository.get_multi(db, skip=skip, limit=limit)
    total = await quota_repository.count(db)

    return APIResponse[QuotaListResponse](
        success=True,
        data=QuotaListResponse(
            items=[QuotaPolicyResponse.model_validate(p) for p in items],
            total=total,
        ),
        correlation_id=get_correlation_id(),
    )


@router.post("/quotas", response_model=APIResponse[QuotaPolicyResponse], status_code=status.HTTP_201_CREATED)
async def create_quota_policy(
    payload: QuotaPolicyCreate,
    db: AsyncSession = Depends(get_db),
    auth: Optional[AuthContext] = Depends(get_optional_auth_context),
) -> APIResponse[QuotaPolicyResponse]:
    """Define a new token quota and budget policy."""
    if auth and not has_sufficient_role(auth.role, "operator"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operator role required")

    existing = await quota_repository.get_by_name(db, payload.name)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Quota policy name already exists")

    created = await quota_repository.create(db, payload)
    return APIResponse[QuotaPolicyResponse](
        success=True,
        data=QuotaPolicyResponse.model_validate(created),
        message="Quota policy created successfully",
        correlation_id=get_correlation_id(),
    )


@router.get("/quotas/{policy_id}", response_model=APIResponse[QuotaPolicyResponse])
async def get_quota_policy(
    policy_id: str,
    db: AsyncSession = Depends(get_db),
    auth: Optional[AuthContext] = Depends(get_optional_auth_context),
) -> APIResponse[QuotaPolicyResponse]:
    """Fetch details of a single quota policy."""
    policy = await quota_repository.get(db, policy_id)
    if not policy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quota policy not found")

    return APIResponse[QuotaPolicyResponse](
        success=True,
        data=QuotaPolicyResponse.model_validate(policy),
        correlation_id=get_correlation_id(),
    )


@router.get("/quotas/{policy_id}/usage", response_model=APIResponse[QuotaUsageSummary])
async def get_quota_usage_summary(
    policy_id: str,
    db: AsyncSession = Depends(get_db),
    auth: Optional[AuthContext] = Depends(get_optional_auth_context),
) -> APIResponse[QuotaUsageSummary]:
    """Inspect live consumption rates and remaining token balance for a quota policy."""
    policy = await quota_repository.get(db, policy_id)
    if not policy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quota policy not found")

    summary = quota_repository.get_summary(policy)
    return APIResponse[QuotaUsageSummary](
        success=True,
        data=summary,
        correlation_id=get_correlation_id(),
    )


@router.put("/quotas/{policy_id}", response_model=APIResponse[QuotaPolicyResponse])
async def update_quota_policy(
    policy_id: str,
    payload: QuotaPolicyUpdate,
    db: AsyncSession = Depends(get_db),
    auth: Optional[AuthContext] = Depends(get_optional_auth_context),
) -> APIResponse[QuotaPolicyResponse]:
    """Update quota rules, limits, or active state."""
    if auth and not has_sufficient_role(auth.role, "operator"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operator role required")

    policy = await quota_repository.get(db, policy_id)
    if not policy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quota policy not found")

    updated = await quota_repository.update(db, db_obj=policy, obj_in=payload)
    return APIResponse[QuotaPolicyResponse](
        success=True,
        data=QuotaPolicyResponse.model_validate(updated),
        message="Quota policy updated successfully",
        correlation_id=get_correlation_id(),
    )


@router.post("/quotas/{policy_id}/reset", response_model=APIResponse[QuotaUsageSummary])
async def reset_quota_counters(
    policy_id: str,
    db: AsyncSession = Depends(get_db),
    auth: Optional[AuthContext] = Depends(get_optional_auth_context),
) -> APIResponse[QuotaUsageSummary]:
    """Manually reset daily and monthly token consumption meters."""
    if auth and not has_sufficient_role(auth.role, "operator"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operator role required")

    policy = await quota_repository.get(db, policy_id)
    if not policy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quota policy not found")

    policy.used_tokens_today = 0
    policy.used_tokens_this_month = 0
    await db.commit()
    await db.refresh(policy)

    summary = quota_repository.get_summary(policy)
    return APIResponse[QuotaUsageSummary](
        success=True,
        data=summary,
        message="Quota counters reset to zero",
        correlation_id=get_correlation_id(),
    )


@router.delete("/quotas/{policy_id}", response_model=APIResponse[dict])
async def delete_quota_policy(
    policy_id: str,
    db: AsyncSession = Depends(get_db),
    auth: Optional[AuthContext] = Depends(get_optional_auth_context),
) -> APIResponse[dict]:
    """Remove a quota policy definition."""
    if auth and not has_sufficient_role(auth.role, "operator"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operator role required")

    policy = await quota_repository.get(db, policy_id)
    if not policy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quota policy not found")

    await quota_repository.delete(db, id=policy_id)
    await db.commit()
    return APIResponse[dict](
        success=True,
        data={"deleted_id": policy_id},
        message="Quota policy removed",
        correlation_id=get_correlation_id(),
    )
