"""API Key Management Endpoints for InferX."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import (
    AuthContext,
    get_current_auth,
    record_audit_log,
    require_role,
)
from backend.app.api.v1.schemas import APIResponse
from backend.app.core.logging import get_correlation_id
from backend.app.db.session import get_db
from backend.app.repositories.api_key_repository import api_key_repository
from backend.app.schemas.api_key import (
    ApiKeyCreate,
    ApiKeyCreatedResponse,
    ApiKeyListResponse,
    ApiKeyResponse,
)

router = APIRouter()


@router.post(
    "",
    response_model=APIResponse[ApiKeyCreatedResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("operator"))],
)
async def create_api_key(
    payload: ApiKeyCreate,
    request: Request,
    auth: AuthContext = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[ApiKeyCreatedResponse]:
    """
    Generate a new API key with configured rate limits and RBAC role.
    The plaintext raw_key is returned ONLY once in this response.
    """
    user_id = auth.user.id if auth.user else None
    key_entity, raw_key = await api_key_repository.create_api_key(
        db=db,
        payload=payload,
        user_id=user_id,
    )

    await record_audit_log(
        db=db,
        request=request,
        auth=auth,
        action="api_key.create",
        resource_type="api_key",
        resource_id=key_entity.id,
        details={"name": key_entity.name, "role": key_entity.role, "prefix": key_entity.prefix},
    )

    response_data = ApiKeyCreatedResponse(
        id=key_entity.id,
        name=key_entity.name,
        prefix=key_entity.prefix,
        role=key_entity.role,
        is_active=key_entity.is_active,
        rate_limit_rps=key_entity.rate_limit_rps,
        expires_at=key_entity.expires_at,
        user_id=key_entity.user_id,
        created_at=key_entity.created_at,
        updated_at=key_entity.updated_at,
        raw_key=raw_key,
    )

    return APIResponse[ApiKeyCreatedResponse](
        success=True,
        data=response_data,
        correlation_id=get_correlation_id(),
    )


@router.get(
    "",
    response_model=APIResponse[ApiKeyListResponse],
    dependencies=[Depends(require_role("viewer"))],
)
async def list_api_keys(
    is_active: Optional[bool] = Query(None, description="Filter by active state"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    auth: AuthContext = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[ApiKeyListResponse]:
    """List API keys with pagination (raw secret keys are never returned)."""
    # Non-admins only see their own keys
    target_user_id = None if auth.role == "admin" else (auth.user.id if auth.user else None)

    items = await api_key_repository.list_keys(
        db=db,
        user_id=target_user_id,
        is_active=is_active,
        skip=skip,
        limit=limit,
    )
    total = await api_key_repository.count_keys(
        db=db,
        user_id=target_user_id,
        is_active=is_active,
    )

    return APIResponse[ApiKeyListResponse](
        success=True,
        data=ApiKeyListResponse(
            items=[ApiKeyResponse.model_validate(k) for k in items],
            total=total,
            skip=skip,
            limit=limit,
        ),
        correlation_id=get_correlation_id(),
    )


@router.delete(
    "/{key_id}",
    response_model=APIResponse[ApiKeyResponse],
    dependencies=[Depends(require_role("operator"))],
)
async def revoke_api_key(
    key_id: str,
    request: Request,
    auth: AuthContext = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[ApiKeyResponse]:
    """Revoke an active API key, instantly disabling its gateway access."""
    key = await api_key_repository.get(db, key_id)
    if not key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"API key with ID '{key_id}' not found",
        )

    # Only admins can revoke keys belonging to other users
    if auth.role != "admin" and auth.user and key.user_id and key.user_id != auth.user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot revoke an API key owned by another user",
        )

    revoked = await api_key_repository.revoke(db, key_id)

    await record_audit_log(
        db=db,
        request=request,
        auth=auth,
        action="api_key.revoke",
        resource_type="api_key",
        resource_id=key_id,
        details={"name": key.name, "prefix": key.prefix},
    )

    return APIResponse[ApiKeyResponse](
        success=True,
        data=ApiKeyResponse.model_validate(revoked),
        correlation_id=get_correlation_id(),
    )
