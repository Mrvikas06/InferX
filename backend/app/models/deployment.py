"""Deployment SQLAlchemy ORM Model for InferX."""

from typing import TYPE_CHECKING, Optional

from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from backend.app.models.model import Model


class Deployment(Base, UUIDMixin, TimestampMixin):
    """Represents a serving instance endpoint associated with a registered model."""

    __tablename__ = "deployments"

    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    model_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("models.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    engine: Mapped[str] = mapped_column(String(32), default="vLLM", nullable=False)
    tensor_parallel: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    port: Mapped[int] = mapped_column(Integer, unique=True, nullable=False, index=True)
    max_model_len: Mapped[int] = mapped_column(Integer, default=8192, nullable=False)
    gpu_type: Mapped[str] = mapped_column(String(128), default="Auto-detect", nullable=False)
    kv_cache_usage: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    qps: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="stopped", nullable=False, index=True)
    replicas: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    base_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Relationships
    model: Mapped["Model"] = relationship(
        "Model",
        back_populates="deployments",
        lazy="joined",
    )
