"""Data access repository for Autoscaling policies."""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

try:
    from backend.app.models.scaling import ScalingPolicy
    from backend.app.schemas.scaling import ScalingPolicyCreate, ScalingPolicyUpdate
except (ImportError, ModuleNotFoundError):
    from app.models.scaling import ScalingPolicy
    from app.schemas.scaling import ScalingPolicyCreate, ScalingPolicyUpdate


class ScalingRepository:
    """Repository operations for deployment scaling policies."""

    async def get_by_deployment_id(
        self, db: AsyncSession, deployment_id: str
    ) -> Optional[ScalingPolicy]:
        """Fetch scaling policy by deployment ID."""
        query = select(ScalingPolicy).where(ScalingPolicy.deployment_id == deployment_id)
        result = await db.execute(query)
        return result.scalars().first()

    async def create_or_update_policy(
        self,
        db: AsyncSession,
        deployment_id: str,
        data: ScalingPolicyCreate | ScalingPolicyUpdate,
    ) -> ScalingPolicy:
        """Create new policy or update existing one for a deployment."""
        existing = await self.get_by_deployment_id(db, deployment_id)
        update_data = data.model_dump(exclude_unset=True)

        if existing:
            for key, value in update_data.items():
                if value is not None:
                    setattr(existing, key, value)
            policy = existing
        else:
            policy = ScalingPolicy(
                deployment_id=deployment_id,
                min_replicas=update_data.get("min_replicas", 1),
                max_replicas=update_data.get("max_replicas", 5),
                target_metric=update_data.get("target_metric", "qps"),
                target_value=update_data.get("target_value", 50.0),
                scale_up_cooldown=update_data.get("scale_up_cooldown", 60),
                scale_down_cooldown=update_data.get("scale_down_cooldown", 180),
                is_enabled=update_data.get("is_enabled", True),
            )
            db.add(policy)

        await db.commit()
        await db.refresh(policy)
        return policy

    async def record_scale_event(
        self,
        db: AsyncSession,
        deployment_id: str,
        action: str,
    ) -> Optional[ScalingPolicy]:
        """Record timestamp and description of an autoscaling action."""
        existing = await self.get_by_deployment_id(db, deployment_id)
        if existing:
            existing.last_scale_at = datetime.now(timezone.utc)
            existing.last_scale_action = action
            await db.commit()
            await db.refresh(existing)
        return existing


scaling_repository = ScalingRepository()
