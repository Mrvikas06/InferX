"""Telemetry and Hardware Observability API Endpoints."""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

try:
    from backend.app.api.deps import AuthContext, get_optional_auth_context
    from backend.app.api.v1.schemas import APIResponse
    from backend.app.core.logging import get_correlation_id
    from backend.app.db.session import get_db
    from backend.app.repositories.deployment_repository import deployment_repository
    from backend.app.schemas.telemetry import (
        GPUStats,
        HistoricalMetricPoint,
        InferenceMetricsSnapshot,
        SystemResourceStats,
        TelemetryOverviewResponse,
    )
    from backend.app.services.gpu_monitor import get_gpu_telemetry, get_system_resources
    from backend.app.services.telemetry_service import telemetry_service
except (ImportError, ModuleNotFoundError):
    from app.api.deps import AuthContext, get_optional_auth_context
    from app.api.v1.schemas import APIResponse
    from app.core.logging import get_correlation_id
    from app.db.session import get_db
    from app.repositories.deployment_repository import deployment_repository
    from app.schemas.telemetry import (
        GPUStats,
        HistoricalMetricPoint,
        InferenceMetricsSnapshot,
        SystemResourceStats,
        TelemetryOverviewResponse,
    )
    from app.services.gpu_monitor import get_gpu_telemetry, get_system_resources
    from app.services.telemetry_service import telemetry_service

logger = logging.getLogger("inferx.api.telemetry")

router = APIRouter()


@router.get(
    "/overview",
    response_model=APIResponse[TelemetryOverviewResponse],
    summary="Get aggregated telemetry overview",
)
async def get_telemetry_overview(
    request: Request,
    db: AsyncSession = Depends(get_db),
    auth: Optional[AuthContext] = Depends(get_optional_auth_context),
):
    """Retrieve combined snapshot of GPU hardware, host system resources, and inference metrics."""
    correlation_id = get_correlation_id()
    active_deps = await deployment_repository.get_active(db)
    active_count = len([d for d in active_deps if d.status == "running"])

    gpus = get_gpu_telemetry()
    system = get_system_resources()
    inference = telemetry_service.get_live_inference_snapshot(active_deployments_count=active_count)

    overview = TelemetryOverviewResponse(
        gpus=gpus,
        system=system,
        inference=inference,
    )

    return APIResponse[TelemetryOverviewResponse](
        success=True,
        data=overview,
        correlation_id=correlation_id,
    )


@router.get(
    "/gpus",
    response_model=APIResponse[List[GPUStats]],
    summary="Get GPU hardware statistics",
)
async def get_gpus_status(
    request: Request,
    auth: Optional[AuthContext] = Depends(get_optional_auth_context),
):
    """Retrieve real-time VRAM allocation, compute utilization, temperature, and power for all GPUs."""
    correlation_id = get_correlation_id()
    gpus = get_gpu_telemetry()
    return APIResponse[List[GPUStats]](
        success=True,
        data=gpus,
        correlation_id=correlation_id,
    )


@router.get(
    "/system",
    response_model=APIResponse[SystemResourceStats],
    summary="Get host system resources",
)
async def get_system_status(
    request: Request,
    auth: Optional[AuthContext] = Depends(get_optional_auth_context),
):
    """Retrieve CPU, RAM, and Disk metrics of the host machine."""
    correlation_id = get_correlation_id()
    sys_metrics = get_system_resources()
    return APIResponse[SystemResourceStats](
        success=True,
        data=sys_metrics,
        correlation_id=correlation_id,
    )


@router.get(
    "/metrics",
    response_model=APIResponse[InferenceMetricsSnapshot],
    summary="Get live inference throughput and latency",
)
async def get_inference_metrics(
    request: Request,
    db: AsyncSession = Depends(get_db),
    auth: Optional[AuthContext] = Depends(get_optional_auth_context),
):
    """Retrieve live QPS, token throughput rate, and p50/p95/p99 latency percentiles."""
    correlation_id = get_correlation_id()
    active_deps = await deployment_repository.get_active(db)
    active_count = len([d for d in active_deps if d.status == "running"])
    metrics = telemetry_service.get_live_inference_snapshot(active_deployments_count=active_count)

    return APIResponse[InferenceMetricsSnapshot](
        success=True,
        data=metrics,
        correlation_id=correlation_id,
    )


@router.get(
    "/history",
    response_model=APIResponse[List[HistoricalMetricPoint]],
    summary="Get historical timeseries metrics",
)
async def get_metrics_history(
    request: Request,
    auth: Optional[AuthContext] = Depends(get_optional_auth_context),
):
    """Retrieve recent time-series data points for telemetry graphs and charts."""
    correlation_id = get_correlation_id()
    history = telemetry_service.get_historical_telemetry()
    return APIResponse[List[HistoricalMetricPoint]](
        success=True,
        data=history,
        correlation_id=correlation_id,
    )
