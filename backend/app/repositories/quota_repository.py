"""Quota Policy Data Access and Token Metering Repository."""

from datetime import datetime, timezone
from typing import List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

try:
    from backend.app.models.quota import QuotaPolicy
    from backend.app.repositories.base import BaseRepository
    from backend.app.schemas.quota import QuotaPolicyCreate, QuotaPolicyUpdate, QuotaUsageSummary
except (ImportError, ModuleNotFoundError):
    from app.models.quota import QuotaPolicy
    from app.repositories.base import BaseRepository
    from app.schemas.quota import QuotaPolicyCreate, QuotaPolicyUpdate, QuotaUsageSummary


class QuotaRepository(BaseRepository[QuotaPolicy, QuotaPolicyCreate, QuotaPolicyUpdate]):
    """Data access and consumption ledger for QuotaPolicy entities."""

    def __init__(self):
        super().__init__(QuotaPolicy)

    async def get_by_name(self, db: AsyncSession, name: str) -> Optional[QuotaPolicy]:
        """Fetch quota policy by unique name."""
        stmt = select(QuotaPolicy).where(QuotaPolicy.name == name)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_target(
        self, db: AsyncSession, target_type: str, target_id: Optional[str] = None
    ) -> Optional[QuotaPolicy]:
        """Fetch the most specific quota policy for a user, api_key, or tenant."""
        if target_id:
            stmt = select(QuotaPolicy).where(
                QuotaPolicy.target_type == target_type,
                QuotaPolicy.target_id == target_id,
                QuotaPolicy.is_active == True,
            )
            result = await db.execute(stmt)
            policy = result.scalar_one_or_none()
            if policy:
                return policy

        # Fallback to default/global policy for this target_type
        stmt = select(QuotaPolicy).where(
            QuotaPolicy.target_type == target_type,
            QuotaPolicy.target_id.is_(None),
            QuotaPolicy.is_active == True,
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def check_quota(
        self,
        db: AsyncSession,
        target_type: str,
        target_id: Optional[str] = None,
        estimated_tokens: int = 100,
    ) -> Tuple[bool, str, int]:
        """
        Check if the subject is permitted to consume tokens.
        Returns: (is_allowed, reason, remaining_daily_tokens)
        """
        policy = await self.get_by_target(db, target_type, target_id)
        if not policy or not policy.is_active:
            # No quota configured or inactive -> allow
            return True, "No quota constraint", 999_999_999

        now = datetime.now(timezone.utc)
        # Check if day has rolled over
        if policy.last_reset_at and now.date() > policy.last_reset_at.date():
            policy.used_tokens_today = 0
            if now.month != policy.last_reset_at.month:
                policy.used_tokens_this_month = 0
            policy.last_reset_at = now
            await db.commit()
            await db.refresh(policy)

        # Enforce daily limit
        if policy.used_tokens_today + estimated_tokens > policy.max_tokens_per_day:
            remaining = max(0, policy.max_tokens_per_day - policy.used_tokens_today)
            return False, f"Daily token quota exceeded ({policy.used_tokens_today}/{policy.max_tokens_per_day})", remaining

        # Enforce monthly limit
        if policy.used_tokens_this_month + estimated_tokens > policy.max_tokens_per_month:
            remaining = max(0, policy.max_tokens_per_month - policy.used_tokens_this_month)
            return False, f"Monthly token quota exceeded ({policy.used_tokens_this_month}/{policy.max_tokens_per_month})", remaining

        remaining = max(0, policy.max_tokens_per_day - policy.used_tokens_today)
        return True, "Quota budget available", remaining

    async def record_consumption(
        self,
        db: AsyncSession,
        target_type: str,
        target_id: Optional[str],
        tokens_consumed: int,
    ) -> Optional[QuotaPolicy]:
        """Atomically record consumed prompt and completion tokens against quota budget."""
        policy = await self.get_by_target(db, target_type, target_id)
        if not policy:
            return None

        policy.used_tokens_today += tokens_consumed
        policy.used_tokens_this_month += tokens_consumed
        policy.total_requests_count += 1
        policy.last_reset_at = datetime.now(timezone.utc)

        await db.commit()
        await db.refresh(policy)
        return policy

    def get_summary(self, policy: QuotaPolicy) -> QuotaUsageSummary:
        """Calculate percentage metrics and remaining budget."""
        daily_rem = max(0, policy.max_tokens_per_day - policy.used_tokens_today)
        monthly_rem = max(0, policy.max_tokens_per_month - policy.used_tokens_this_month)
        daily_pct = round((policy.used_tokens_today / max(1, policy.max_tokens_per_day)) * 100.0, 2)
        monthly_pct = round((policy.used_tokens_this_month / max(1, policy.max_tokens_per_month)) * 100.0, 2)

        return QuotaUsageSummary(
            policy_id=policy.id,
            policy_name=policy.name,
            target_type=policy.target_type,
            target_id=policy.target_id,
            daily_quota=policy.max_tokens_per_day,
            daily_used=policy.used_tokens_today,
            daily_remaining=daily_rem,
            daily_usage_pct=min(100.0, daily_pct),
            monthly_quota=policy.max_tokens_per_month,
            monthly_used=policy.used_tokens_this_month,
            monthly_remaining=monthly_rem,
            monthly_usage_pct=min(100.0, monthly_pct),
            rate_limit_rpm=policy.rate_limit_rpm,
            is_exhausted=(daily_rem <= 0 or monthly_rem <= 0),
        )


quota_repository = QuotaRepository()
