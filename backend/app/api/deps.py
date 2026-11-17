"""Authentication, Authorization, and RBAC Dependencies for InferX."""

from dataclasses import dataclass
from typing import Callable, Optional

from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.security import decode_token, has_sufficient_role
from backend.app.db.session import get_db
from backend.app.models.api_key import ApiKey
from backend.app.models.user import User
from backend.app.repositories.api_key_repository import api_key_repository
from backend.app.repositories.audit_log_repository import audit_log_repository
from backend.app.repositories.user_repository import user_repository


@dataclass
class AuthContext:
    """Carries authenticated subject context, role, and source across requests."""

    actor_id: str
    actor_type: str  # "user" | "api_key"
    role: str  # "admin" | "operator" | "viewer"
    user: Optional[User] = None
    api_key: Optional[ApiKey] = None


async def get_optional_auth_context(
    request: Request,
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
) -> Optional[AuthContext]:
    """Inspect request headers to resolve optional User or ApiKey identity."""
    token: Optional[str] = None

    if x_api_key:
        token = x_api_key.strip()
    elif authorization:
        parts = authorization.strip().split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            token = parts[1]

    if not token:
        return None

    # 1. Check if token is an InferX API key
    if token.startswith("ifx_live_"):
        key_entity = await api_key_repository.verify_raw_key(db, token)
        if not key_entity:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid, revoked, or expired API key",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return AuthContext(
            actor_id=key_entity.id,
            actor_type="api_key",
            role=key_entity.role,
            api_key=key_entity,
            user=key_entity.user,
        )

    # 2. Otherwise treat token as JWT access token
    try:
        payload = decode_token(token)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        )

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type: expected access token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed token claims: missing subject",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await user_repository.get(db, user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account does not exist or has been deactivated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return AuthContext(
        actor_id=user.id,
        actor_type="user",
        role=user.role,
        user=user,
    )


async def get_current_auth(
    auth: Optional[AuthContext] = Depends(get_optional_auth_context),
) -> AuthContext:
    """Enforce authentication on protected routes."""
    if not auth:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return auth


def require_role(min_role: str) -> Callable:
    """Factory creating an RBAC enforcement dependency."""

    async def role_checker(auth: AuthContext = Depends(get_current_auth)) -> AuthContext:
        if not has_sufficient_role(auth.role, min_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation requires '{min_role}' role or higher. Your role is '{auth.role}'.",
            )
        return auth

    return role_checker


async def record_audit_log(
    db: AsyncSession,
    request: Request,
    auth: Optional[AuthContext],
    action: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    status: str = "success",
    details: Optional[dict] = None,
) -> None:
    """Helper to log security and administrative actions."""
    actor_id = auth.actor_id if auth else "anonymous"
    ip = request.client.host if request.client else None
    await audit_log_repository.record(
        db=db,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        actor_id=actor_id,
        status=status,
        details=details or {},
        ip_address=ip,
    )
