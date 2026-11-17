"""Inference Benchmarking and Load Testing API Endpoints."""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

try:
    from backend.app.api.deps import AuthContext, get_optional_auth_context, require_role
    from backend.app.api.v1.schemas import APIResponse
    from backend.app.core.logging import get_correlation_id
    from backend.app.db.session import get_db
    from backend.app.repositories.benchmark_repository import benchmark_repository
    from backend.app.repositories.deployment_repository import deployment_repository
    from backend.app.schemas.benchmark import (
        BenchmarkCreate,
        BenchmarkListResponse,
        BenchmarkResponse,
    )
    from backend.app.services.benchmark_runner import launch_benchmark_background
except (ImportError, ModuleNotFoundError):
    from app.api.deps import AuthContext, get_optional_auth_context, require_role
    from app.api.v1.schemas import APIResponse
    from app.core.logging import get_correlation_id
    from app.db.session import get_db
    from app.repositories.benchmark_repository import benchmark_repository
    from app.repositories.deployment_repository import deployment_repository
    from app.schemas.benchmark import (
        BenchmarkCreate,
        BenchmarkListResponse,
        BenchmarkResponse,
    )
    from app.services.benchmark_runner import launch_benchmark_background

logger = logging.getLogger("inferx.api.benchmarks")

router = APIRouter()


def _format_benchmark_response(bm) -> BenchmarkResponse:
    """Format ORM Benchmark into Pydantic schema with parent names."""
    return BenchmarkResponse(
        id=bm.id,
        name=bm.name,
        deployment_id=bm.deployment_id,
        model_id=bm.model_id,
        status=bm.status,
        engine=bm.engine,
        concurrency=bm.concurrency,
        num_prompts=bm.num_prompts,
        input_tokens=bm.input_tokens,
        output_tokens=bm.output_tokens,
        rps=bm.rps,
        tokens_per_sec=bm.tokens_per_sec,
        p50_latency_ms=bm.p50_latency_ms,
        p95_latency_ms=bm.p95_latency_ms,
        p99_latency_ms=bm.p99_latency_ms,
        p50_ttft_ms=bm.p50_ttft_ms,
        p99_ttft_ms=bm.p99_ttft_ms,
        mean_tpot_ms=bm.mean_tpot_ms,
        vram_peak_gb=bm.vram_peak_gb,
        error_count=bm.error_count,
        results_json=bm.results_json,
        created_at=bm.created_at,
        updated_at=bm.updated_at,
        model_name=bm.model.repo_id if bm.model else None,
        deployment_name=bm.deployment.name if bm.deployment else None,
    )


@router.post(
    "",
    response_model=APIResponse[BenchmarkResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Trigger new benchmark run",
)
async def create_benchmark(
    request: Request,
    payload: BenchmarkCreate,
    db: AsyncSession = Depends(get_db),
    auth: Optional[AuthContext] = Depends(get_optional_auth_context),
):
    """Initiate an automated inference benchmark and concurrency sweep."""
    correlation_id = get_correlation_id()

    # Verify target deployment exists
    deployment = await deployment_repository.get_with_model(db, payload.deployment_id)
    if not deployment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Target deployment '{payload.deployment_id}' not found.",
        )

    # Persist benchmark entity
    from backend.app.models.benchmark import Benchmark

    bm = Benchmark(
        name=payload.name,
        deployment_id=payload.deployment_id,
        model_id=deployment.model_id,
        status="queued",
        engine=deployment.engine,
        concurrency=payload.concurrency,
        num_prompts=payload.num_prompts,
        input_tokens=payload.input_tokens,
        output_tokens=payload.output_tokens,
        results_json={},
    )
    db.add(bm)
    await db.flush()
    await db.refresh(bm)

    # Launch background worker
    launch_benchmark_background(bm.id)

    formatted = _format_benchmark_response(bm)
    return APIResponse[BenchmarkResponse](
        success=True,
        data=formatted,
        correlation_id=correlation_id,
    )


@router.get(
    "",
    response_model=APIResponse[BenchmarkListResponse],
    summary="List benchmark runs",
)
async def list_benchmarks(
    request: Request,
    deployment_id: Optional[str] = Query(None, description="Filter by deployment UUID"),
    status: Optional[str] = Query(None, description="Filter by status (queued, running, completed, failed)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    auth: Optional[AuthContext] = Depends(get_optional_auth_context),
):
    """Retrieve historical benchmark runs with throughput and latency percentiles."""
    correlation_id = get_correlation_id()

    items = await benchmark_repository.list_benchmarks(
        db, deployment_id=deployment_id, status=status, skip=skip, limit=limit
    )
    total = await benchmark_repository.count_filtered(db, deployment_id=deployment_id, status=status)

    formatted_items = [_format_benchmark_response(item) for item in items]
    return APIResponse[BenchmarkListResponse](
        success=True,
        data=BenchmarkListResponse(total=total, items=formatted_items),
        correlation_id=correlation_id,
    )


@router.get(
    "/{id}",
    response_model=APIResponse[BenchmarkResponse],
    summary="Retrieve single benchmark report",
)
async def get_benchmark(
    id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    auth: Optional[AuthContext] = Depends(get_optional_auth_context),
):
    """Retrieve detailed results, latency histogram, and TTFT distribution for a benchmark."""
    correlation_id = get_correlation_id()
    bm = await benchmark_repository.get_with_relations(db, id)
    if not bm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Benchmark '{id}' not found.",
        )

    formatted = _format_benchmark_response(bm)
    return APIResponse[BenchmarkResponse](
        success=True,
        data=formatted,
        correlation_id=correlation_id,
    )


@router.delete(
    "/{id}",
    response_model=APIResponse[dict],
    summary="Delete benchmark record",
)
async def delete_benchmark(
    id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    auth: Optional[AuthContext] = Depends(get_optional_auth_context),
):
    """Remove a benchmark record and its results."""
    correlation_id = get_correlation_id()
    deleted = await benchmark_repository.delete(db, id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Benchmark '{id}' not found.",
        )

    return APIResponse[dict](
        success=True,
        data={"deleted": id},
        correlation_id=correlation_id,
    )
