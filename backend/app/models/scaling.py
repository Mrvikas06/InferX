"""Autoscaling Policy SQLAlchemy ORM Model for InferX."""

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

try:
    from backend.app.db.base import Base, TimestampMixin, UUIDMixin
except (ImportError, ModuleNotFoundError):
    from app.db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    try:
        from backend.app.models.deployment import Deployment
    except (ImportError, ModuleNotFoundError):
        from app.models.deployment import Deployment


class ScalingPolicy(Base, UUIDMixin, TimestampMixin):
    """Autoscaling rules and thresholds for a specific model deployment."""

    __tablename__ = "scaling_policies"

    deployment_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("deployments.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    min_replicas: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    max_replicas: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    target_metric: Mapped[str] = mapped_column(String(32), default="qps", nullable=False)
    target_value: Mapped[float] = mapped_column(Float, default=50.0, nullable=False)
    scale_up_cooldown: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    scale_down_cooldown: Mapped[int] = mapped_column(Integer, default=180, nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_scale_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    last_scale_action: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    # Relationships
    deployment: Mapped["Deployment"] = relationship(
        "Deployment",
        back_populates="scaling_policy",
        lazy="joined",
    )
