"""Model Repository handling data access for registered LLMs."""

from typing import List, Optional

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.model import Model
from backend.app.repositories.base import BaseRepository
from backend.app.schemas.model import ModelCreate, ModelUpdate


class ModelRepository(BaseRepository[Model, ModelCreate, ModelUpdate]):
    """Data access repository for Model entities."""

    async def get_by_repo_id(self, db: AsyncSession, repo_id: str) -> Optional[Model]:
        """Fetch a model by its unique HuggingFace repository identifier."""
        query = select(Model).where(Model.repo_id == repo_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_name(self, db: AsyncSession, name: str) -> Optional[Model]:
        """Fetch a model by its display name."""
        query = select(Model).where(Model.name == name)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def search_models(
        self,
        db: AsyncSession,
        query_str: Optional[str] = None,
        precision: Optional[str] = None,
        is_downloaded: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Model]:
        """Search and filter registered models by keywords, precision, and download status."""
        stmt = select(Model)

        if query_str:
            pattern = f"%{query_str}%"
            stmt = stmt.where(
                or_(
                    Model.name.ilike(pattern),
                    Model.repo_id.ilike(pattern),
                    Model.architecture.ilike(pattern),
                )
            )

        if precision:
            stmt = stmt.where(Model.precision.ilike(precision))

        if is_downloaded is not None:
            stmt = stmt.where(Model.is_downloaded == is_downloaded)

        stmt = stmt.order_by(Model.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def count_filtered(
        self,
        db: AsyncSession,
        query_str: Optional[str] = None,
        precision: Optional[str] = None,
        is_downloaded: Optional[bool] = None,
    ) -> int:
        """Count models matching specified filter criteria."""
        stmt = select(func.count(Model.id))

        if query_str:
            pattern = f"%{query_str}%"
            stmt = stmt.where(
                or_(
                    Model.name.ilike(pattern),
                    Model.repo_id.ilike(pattern),
                    Model.architecture.ilike(pattern),
                )
            )

        if precision:
            stmt = stmt.where(Model.precision.ilike(precision))

        if is_downloaded is not None:
            stmt = stmt.where(Model.is_downloaded == is_downloaded)

        result = await db.execute(stmt)
        return result.scalar() or 0


model_repository = ModelRepository(Model)
