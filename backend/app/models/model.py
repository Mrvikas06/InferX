"""Model Registry SQLAlchemy ORM Model for InferX."""

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sqlalchemy import Boolean, Float, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from backend.app.models.deployment import Deployment


class Model(Base, UUIDMixin, TimestampMixin):
    """Stores LLM metadata, precision, architecture, and disk cache state."""

    __tablename__ = "models"

    name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    repo_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    architecture: Mapped[str] = mapped_column(String(128), default="AutoModelForCausalLM", nullable=False)
    parameters: Mapped[str] = mapped_column(String(32), default="Unknown", nullable=False)
    context_window: Mapped[int] = mapped_column(Integer, default=8192, nullable=False)
    precision: Mapped[str] = mapped_column(String(16), default="BF16", nullable=False, index=True)
    size_on_disk_gb: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    min_gpu_vram_gb: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    local_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    is_downloaded: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    tags: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    metadata_json: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    # Relationships
    deployments: Mapped[List["Deployment"]] = relationship(
        "Deployment",
        back_populates="model",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
