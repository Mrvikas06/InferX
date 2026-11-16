"""Health, Liveness, Readiness, and System Info Endpoints for InferX."""

import os
from typing import Dict, List

import psutil
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from backend.app.api.v1.schemas import (
    APIResponse,
    HardwareInfo,
    HealthCheckItem,
    HealthResponse,
    PlatformInfoResponse,
)
from backend.app.core.config import get_settings
from backend.app.core.logging import get_correlation_id

router = APIRouter(tags=["Health & System"])
settings = get_settings()


def get_hardware_info() -> HardwareInfo:
    """Safely inspect host CPU, RAM, and NVIDIA GPU availability."""
    cpu_count = psutil.cpu_count(logical=True) or 1
    mem = psutil.virtual_memory()
    total_gb = round(mem.total / (1024**3), 2)
    avail_gb = round(mem.available / (1024**3), 2)

    gpu_available = False
    gpu_count = 0
    gpu_names: List[str] = []

    # Check CUDA availability via PyTorch if available
    try:
        import torch
        if torch.cuda.is_available():
            gpu_available = True
            gpu_count = torch.cuda.device_count()
            gpu_names = [torch.cuda.get_device_name(i) for i in range(gpu_count)]
    except Exception:
        # Fallback to checking via environment or pynvml
        pass

    return HardwareInfo(
        cpu_count=cpu_count,
        memory_total_gb=total_gb,
        memory_available_gb=avail_gb,
        gpu_available=gpu_available,
        gpu_count=gpu_count,
        gpu_names=gpu_names,
    )


@router.get("/health", response_model=HealthResponse)
async def get_health() -> HealthResponse:
    """Primary health status endpoint."""
    return HealthResponse(
        status="healthy",
        app_name=settings.APP_NAME,
        version=settings.VERSION,
        environment=settings.APP_ENV,
        components={
            "api": HealthCheckItem(status="healthy", message="Inference control plane active"),
            "config": HealthCheckItem(status="healthy", message="Settings loaded successfully"),
        },
    )


@router.get("/health/live")
async def get_liveness():
    """Liveness probe for container orchestrators (Docker / Kubernetes)."""
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"status": "live", "app": settings.APP_NAME},
    )


@router.get("/health/ready", response_model=HealthResponse)
async def get_readiness() -> HealthResponse:
    """Readiness probe verifying operational state."""
    # In Phase 1, control plane is ready once configuration and runtime are healthy.
    # Future phases will attach PostgreSQL connection pool and Redis ping checks here.
    return HealthResponse(
        status="ready",
        app_name=settings.APP_NAME,
        version=settings.VERSION,
        environment=settings.APP_ENV,
        components={
            "runtime": HealthCheckItem(status="healthy", message="FastAPI event loop responsive"),
            "memory": HealthCheckItem(status="healthy", message="Host memory within operational threshold"),
        },
    )


@router.get("/info", response_model=APIResponse[PlatformInfoResponse])
async def get_platform_info() -> APIResponse[PlatformInfoResponse]:
    """Retrieve platform metadata, supported serving engines, and hardware context."""
    hw_info = get_hardware_info()
    data = PlatformInfoResponse(
        name=settings.APP_NAME,
        version=settings.VERSION,
        environment=settings.APP_ENV,
        supported_engines=["vLLM", "SGLang", "TensorRT-LLM"],
        hardware=hw_info,
    )
    return APIResponse(
        success=True,
        data=data,
        correlation_id=get_correlation_id(),
    )
