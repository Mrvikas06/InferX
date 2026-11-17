"""Benchmark SQLAlchemy ORM Model for InferX."""

from typing import TYPE_CHECKING, Any, Dict, Optional

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

try:
    from backend.app.db.base import Base, TimestampMixin, UUIDMixin
except (ImportError, ModuleNotFoundError):
    from app.db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    try:
        from backend.app.models.deployment import Deployment
        from backend.app.models.model import Model
    except (ImportError, ModuleNotFoundError):
        from app.models.model import Model
        from app.models.deployment import Deployment


class Benchmark(Base, UUIDMixin, TimestampMixin):
    """Represents an automated inference benchmark run and load test record."""

    __tablename__ = "benchmarks"

    name: Mapped[str] = mapped_column(String(128), nullable=False)
    deployment_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("deployments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    model_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("models.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    status: Mapped[str] = mapped_column(String(32), default="queued", nullable=False, index=True)
    engine: Mapped[str] = mapped_column(String(32), default="vLLM", nullable=False)
    concurrency: Mapped[int] = mapped_column(Integer, default=16, nullable=False)
    num_prompts: Mapped[int] = mapped_column(Integer, default=64, nullable=False)
    input_tokens: Mapped[int] = mapped_column(Integer, default=256, nullable=False)
    output_tokens: Mapped[int] = mapped_column(Integer, default=128, nullable=False)

    # Performance results
    rps: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    tokens_per_sec: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    p50_latency_ms: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    p95_latency_ms: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    p99_latency_ms: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    p50_ttft_ms: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    p99_ttft_ms: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    mean_tpot_ms: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    vram_peak_gb: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    error_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Detailed trace & percentile distribution
    results_json: Mapped[Dict[str, Any]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        default=dict,
        nullable=False,
    )

    # Relationships
    deployment: Mapped["Deployment"] = relationship(
        "Deployment",
        lazy="joined",
    )
    model: Mapped[Optional["Model"]] = relationship(
        "Model",
        lazy="joined",
    )
