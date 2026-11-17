"""Benchmark Repository handling persistence and query filtering."""

from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

try:
    from backend.app.models.benchmark import Benchmark
    from backend.app.repositories.base import BaseRepository
    from backend.app.schemas.benchmark import BenchmarkCreate
except (ImportError, ModuleNotFoundError):
    from app.models.benchmark import Benchmark
    from app.repositories.base import BaseRepository
    from app.schemas.benchmark import BenchmarkCreate


class BenchmarkRepository(BaseRepository[Benchmark, BenchmarkCreate, BenchmarkCreate]):
    """Data access repository for Benchmark runs."""

    async def get_with_relations(self, db: AsyncSession, id: str) -> Optional[Benchmark]:
        """Fetch benchmark by ID eagerly loading deployment and model relations."""
        stmt = (
            select(Benchmark)
            .options(joinedload(Benchmark.deployment), joinedload(Benchmark.model))
            .where(Benchmark.id == id)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_benchmarks(
        self,
        db: AsyncSession,
        deployment_id: Optional[str] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[Benchmark]:
        """Fetch recent benchmarks with optional deployment or status filters."""
        stmt = (
            select(Benchmark)
            .options(joinedload(Benchmark.deployment), joinedload(Benchmark.model))
            .order_by(Benchmark.created_at.desc())
        )

        if deployment_id:
            stmt = stmt.where(Benchmark.deployment_id == deployment_id)
        if status:
            stmt = stmt.where(Benchmark.status == status)

        stmt = stmt.offset(skip).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def count_filtered(
        self,
        db: AsyncSession,
        deployment_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> int:
        """Count total benchmark records matching filters."""
        stmt = select(func.count(Benchmark.id))
        if deployment_id:
            stmt = stmt.where(Benchmark.deployment_id == deployment_id)
        if status:
            stmt = stmt.where(Benchmark.status == status)
        result = await db.execute(stmt)
        return result.scalar() or 0


benchmark_repository = BenchmarkRepository(Benchmark)
