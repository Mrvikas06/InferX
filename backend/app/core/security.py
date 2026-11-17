"""Cryptographic, Password Hashing, JWT, and API Key Utilities for InferX."""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Tuple

import bcrypt
import jwt

from backend.app.core.config import get_settings

settings = get_settings()

ROLE_HIERARCHY: Dict[str, int] = {
    "admin": 3,
    "operator": 2,
    "viewer": 1,
}


def hash_password(password: str) -> str:
    """Hash plaintext password with bcrypt."""
    rounds = 4 if (settings.is_development or settings.APP_ENV == "testing") else 12
    salt = bcrypt.gensalt(rounds=rounds)
    pwd_bytes = password.encode("utf-8")
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plaintext password against bcrypt hash."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except Exception:
        return False


def create_access_token(
    subject: str,
    role: str = "viewer",
    expires_delta: Optional[timedelta] = None,
    extra_claims: Optional[Dict[str, Any]] = None,
) -> str:
    """Create a signed JWT access token."""
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode: Dict[str, Any] = {
        "sub": str(subject),
        "role": role,
        "type": "access",
        "jti": secrets.token_hex(8),
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    if extra_claims:
        to_encode.update(extra_claims)

    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    return encoded_jwt


def create_refresh_token(
    subject: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a signed JWT refresh token."""
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode: Dict[str, Any] = {
        "sub": str(subject),
        "type": "refresh",
        "jti": secrets.token_hex(8),
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    return encoded_jwt


def decode_token(token: str) -> Dict[str, Any]:
    """Decode and validate a signed JWT token."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError("Token signature has expired")
    except jwt.InvalidTokenError as exc:
        raise ValueError(f"Invalid token: {exc}")


def hash_api_key(raw_key: str) -> str:
    """Compute deterministic SHA-256 hex digest for an API key."""
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


def generate_api_key(name: str = "default") -> Tuple[str, str, str]:
    """
    Generate an InferX API key tuple: (raw_key, prefix, key_hash).
    Format: ifx_live_<prefix>_<secret>
    Only the raw_key is returned once to the user; only key_hash is persisted.
    """
    prefix = secrets.token_hex(4)  # 8 hex chars
    secret = secrets.token_urlsafe(32)  # High entropy random string
    raw_key = f"ifx_live_{prefix}_{secret}"
    key_hash = hash_api_key(raw_key)
    return raw_key, prefix, key_hash


def has_sufficient_role(user_role: str, required_role: str) -> bool:
    """Check if user_role meets or exceeds required_role in the RBAC hierarchy."""
    user_weight = ROLE_HIERARCHY.get(user_role.lower(), 0)
    required_weight = ROLE_HIERARCHY.get(required_role.lower(), 999)
    return user_weight >= required_weight
