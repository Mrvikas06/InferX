"""Token Quota and Governance Policy SQLAlchemy ORM Model for InferX."""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

try:
    from backend.app.db.base import Base, TimestampMixin, UUIDMixin
except (ImportError, ModuleNotFoundError):
    from app.db.base import Base, TimestampMixin, UUIDMixin


class QuotaPolicy(Base, UUIDMixin, TimestampMixin):
    """Stores token budget limits, consumption meters, and rate constraints."""

    __tablename__ = "quota_policies"

    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    target_type: Mapped[str] = mapped_column(String(32), default="user", nullable=False, index=True)
    target_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    max_tokens_per_day: Mapped[int] = mapped_column(Integer, default=1_000_000, nullable=False)
    max_tokens_per_month: Mapped[int] = mapped_column(Integer, default=30_000_000, nullable=False)
    used_tokens_today: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    used_tokens_this_month: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_requests_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rate_limit_rpm: Mapped[int] = mapped_column(Integer, default=120, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_reset_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
