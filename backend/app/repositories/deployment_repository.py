"""Deployment Repository handling endpoint lifecycle and allocation."""

from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

try:
    from backend.app.models.deployment import Deployment
    from backend.app.repositories.base import BaseRepository
    from backend.app.schemas.deployment import DeploymentCreate, DeploymentUpdate
except (ImportError, ModuleNotFoundError):
    from app.models.deployment import Deployment
    from app.repositories.base import BaseRepository
    from app.schemas.deployment import DeploymentCreate, DeploymentUpdate


class DeploymentRepository(BaseRepository[Deployment, DeploymentCreate, DeploymentUpdate]):
    """Data access repository for Deployment entities."""

    async def get_with_model(self, db: AsyncSession, id: str) -> Optional[Deployment]:
        """Fetch deployment by ID with its parent model eagerly loaded."""
        stmt = (
            select(Deployment)
            .options(joinedload(Deployment.model))
            .where(Deployment.id == id)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_name(self, db: AsyncSession, name: str) -> Optional[Deployment]:
        """Fetch deployment by unique name."""
        stmt = (
            select(Deployment)
            .options(joinedload(Deployment.model))
            .where(Deployment.name == name)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_port(self, db: AsyncSession, port: int) -> Optional[Deployment]:
        """Fetch deployment bound to a specific host port."""
        stmt = select(Deployment).where(Deployment.port == port)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_model_id(self, db: AsyncSession, model_id: str) -> List[Deployment]:
        """List all active or registered deployments targeting a model."""
        stmt = (
            select(Deployment)
            .options(joinedload(Deployment.model))
            .where(Deployment.model_id == model_id)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_active(self, db: AsyncSession) -> List[Deployment]:
        """Fetch all running or active deployments."""
        stmt = (
            select(Deployment)
            .options(joinedload(Deployment.model))
            .where(Deployment.status.in_(["running", "starting"]))
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_model_identifier(self, db: AsyncSession, identifier: str) -> List[Deployment]:
        """Find deployments matching a model repo_id, model name, or deployment name."""
        try:
            from backend.app.models.model import Model
        except (ImportError, ModuleNotFoundError):
            from app.models.model import Model

        stmt = (
            select(Deployment)
            .join(Deployment.model, isouter=True)
            .options(joinedload(Deployment.model))
            .where(
                (Deployment.name == identifier)
                | (Model.repo_id == identifier)
                | (Model.name == identifier)
            )
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def list_deployments(
        self,
        db: AsyncSession,
        status: Optional[str] = None,
        engine: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Deployment]:
        """List deployments with filtering and pagination."""
        stmt = select(Deployment).options(joinedload(Deployment.model))

        if status:
            stmt = stmt.where(Deployment.status == status)
        if engine:
            stmt = stmt.where(Deployment.engine.ilike(engine))

        stmt = stmt.order_by(Deployment.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def count_filtered(
        self,
        db: AsyncSession,
        status: Optional[str] = None,
        engine: Optional[str] = None,
    ) -> int:
        """Count deployments matching filtering criteria."""
        stmt = select(func.count(Deployment.id))

        if status:
            stmt = stmt.where(Deployment.status == status)
        if engine:
            stmt = stmt.where(Deployment.engine.ilike(engine))

        result = await db.execute(stmt)
        return result.scalar() or 0


deployment_repository = DeploymentRepository(Deployment)
