"""Authentication Endpoints for User Registration, Login, and Token Rotation."""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import (
    AuthContext,
    get_current_auth,
    record_audit_log,
)
from backend.app.api.v1.schemas import APIResponse
from backend.app.core.config import get_settings
from backend.app.core.logging import get_correlation_id
from backend.app.core.rate_limit import RateLimiter
from backend.app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from backend.app.db.session import get_db
from backend.app.repositories.user_repository import user_repository
from backend.app.schemas.auth import (
    TokenRefresh,
    TokenResponse,
    UserLogin,
    UserRegister,
    UserResponse,
)

router = APIRouter()
settings = get_settings()


@router.post(
    "/register",
    response_model=APIResponse[UserResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RateLimiter(rps=10))],
)
async def register(
    payload: UserRegister,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> APIResponse[UserResponse]:
    """Register a new user account."""
    existing = await user_repository.get_by_email(db, payload.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"An account with email '{payload.email}' already exists",
        )

    # First user can be made admin if none exist, otherwise assigned requested or viewer
    total_users = await user_repository.count(db)
    role_to_assign = "admin" if total_users == 0 else payload.role.lower()
    payload.role = role_to_assign

    user = await user_repository.create_user(db, payload, is_superuser=(role_to_assign == "admin"))

    await record_audit_log(
        db=db,
        request=request,
        auth=None,
        action="user.register",
        resource_type="user",
        resource_id=user.id,
        details={"email": user.email, "role": user.role},
    )

    return APIResponse[UserResponse](
        success=True,
        data=UserResponse.model_validate(user),
        correlation_id=get_correlation_id(),
    )


@router.post(
    "/login",
    response_model=APIResponse[TokenResponse],
    dependencies=[Depends(RateLimiter(rps=20))],
)
async def login(
    payload: UserLogin,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> APIResponse[TokenResponse]:
    """Authenticate with credentials and obtain JWT access and refresh token pair."""
    user = await user_repository.get_by_email(db, payload.email)
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated",
        )

    access_token = create_access_token(subject=user.id, role=user.role)
    refresh_token = create_refresh_token(subject=user.id)

    await record_audit_log(
        db=db,
        request=request,
        auth=None,
        action="user.login",
        resource_type="user",
        resource_id=user.id,
        details={"email": user.email},
    )

    return APIResponse[TokenResponse](
        success=True,
        data=TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        ),
        correlation_id=get_correlation_id(),
    )


@router.post(
    "/refresh",
    response_model=APIResponse[TokenResponse],
    dependencies=[Depends(RateLimiter(rps=20))],
)
async def refresh_token(
    payload: TokenRefresh,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> APIResponse[TokenResponse]:
    """Rotate and refresh an expired or active access token using a valid refresh token."""
    try:
        token_data = decode_token(payload.refresh_token)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid refresh token: {exc}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if token_data.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is not a refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = token_data.get("sub")
    if not user_id or not isinstance(user_id, str):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token subject",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = await user_repository.get(db, user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or deactivated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    new_access_token = create_access_token(subject=user.id, role=user.role)
    new_refresh_token = create_refresh_token(subject=user.id)

    return APIResponse[TokenResponse](
        success=True,
        data=TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        ),
        correlation_id=get_correlation_id(),
    )


@router.get("/me", response_model=APIResponse[UserResponse])
async def get_current_user_profile(
    auth: AuthContext = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[UserResponse]:
    """Get the profile of the currently authenticated user."""
    if not auth.user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current authentication is via API Key, not an interactive User account",
        )
    return APIResponse[UserResponse](
        success=True,
        data=UserResponse.model_validate(auth.user),
        correlation_id=get_correlation_id(),
    )
