"""API Key Repository for Ingestion & Gateway Authentication."""

from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.security import generate_api_key, hash_api_key
from backend.app.models.api_key import ApiKey
from backend.app.repositories.base import BaseRepository
from backend.app.schemas.api_key import ApiKeyCreate


class ApiKeyRepository(BaseRepository[ApiKey, ApiKeyCreate, ApiKeyCreate]):
    """Data access repository for ApiKey entities."""

    async def get_by_hash(self, db: AsyncSession, key_hash: str) -> Optional[ApiKey]:
        """Lookup an API key by its SHA-256 hash."""
        query = select(ApiKey).where(ApiKey.key_hash == key_hash)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_prefix(self, db: AsyncSession, prefix: str) -> List[ApiKey]:
        """Fetch all keys matching a specific prefix."""
        query = select(ApiKey).where(ApiKey.prefix == prefix)
        result = await db.execute(query)
        return list(result.scalars().all())

    async def create_api_key(
        self,
        db: AsyncSession,
        payload: ApiKeyCreate,
        user_id: Optional[str] = None,
    ) -> tuple[ApiKey, str]:
        """
        Generate and persist a new API key.
        Returns a tuple of (persisted ApiKey entity, raw_key string).
        The raw_key is returned ONLY once.
        """
        raw_key, prefix, key_hash = generate_api_key(name=payload.name)
        api_key = ApiKey(
            name=payload.name,
            key_hash=key_hash,
            prefix=prefix,
            role=payload.role.lower(),
            rate_limit_rps=payload.rate_limit_rps,
            expires_at=payload.expires_at,
            user_id=user_id,
            is_active=True,
        )
        db.add(api_key)
        await db.flush()
        await db.refresh(api_key)
        return api_key, raw_key

    async def verify_raw_key(self, db: AsyncSession, raw_key: str) -> Optional[ApiKey]:
        """Verify raw API key, check active state and expiration."""
        if not raw_key.startswith("ifx_live_"):
            return None

        key_hash = hash_api_key(raw_key)
        key = await self.get_by_hash(db, key_hash)
        if not key:
            return None

        if not key.is_active:
            return None

        if key.expires_at:
            # Handle tz-aware expiration comparison
            now = datetime.now(timezone.utc)
            exp = key.expires_at if key.expires_at.tzinfo else key.expires_at.replace(tzinfo=timezone.utc)
            if now > exp:
                return None

        return key

    async def revoke(self, db: AsyncSession, id: str) -> Optional[ApiKey]:
        """Deactivate an API key immediately."""
        key = await self.get(db, id)
        if key:
            key.is_active = False
            db.add(key)
            await db.flush()
            await db.refresh(key)
        return key

    async def list_keys(
        self,
        db: AsyncSession,
        user_id: Optional[str] = None,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[ApiKey]:
        """List keys with filtering and pagination."""
        stmt = select(ApiKey)
        if user_id:
            stmt = stmt.where(ApiKey.user_id == user_id)
        if is_active is not None:
            stmt = stmt.where(ApiKey.is_active == is_active)

        stmt = stmt.order_by(ApiKey.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def count_keys(
        self,
        db: AsyncSession,
        user_id: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> int:
        """Count keys matching filters."""
        stmt = select(func.count(ApiKey.id))
        if user_id:
            stmt = stmt.where(ApiKey.user_id == user_id)
        if is_active is not None:
            stmt = stmt.where(ApiKey.is_active == is_active)

        result = await db.execute(stmt)
        return result.scalar() or 0


api_key_repository = ApiKeyRepository(ApiKey)
