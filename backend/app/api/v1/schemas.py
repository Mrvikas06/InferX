"""API Schema Definitions and Response Envelopes for InferX."""

from datetime import datetime, timezone
from typing import Any, Dict, Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """Standardized API response envelope for all endpoints."""

    success: bool = True
    data: Optional[T] = None
    error: Optional[str] = None
    correlation_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class HealthCheckItem(BaseModel):
    """Component-level health status."""

    status: str
    message: Optional[str] = None
    latency_ms: Optional[float] = None


class HealthResponse(BaseModel):
    """Detailed health check response for liveness and readiness probes."""

    status: str
    app_name: str
    version: str
    environment: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    components: Dict[str, HealthCheckItem] = Field(default_factory=dict)


class HardwareInfo(BaseModel):
    """Host machine hardware context."""

    cpu_count: int
    memory_total_gb: float
    memory_available_gb: float
    gpu_available: bool
    gpu_count: int = 0
    gpu_names: List[str] = Field(default_factory=list)


class PlatformInfoResponse(BaseModel):
    """InferX platform, engine support, and environment metadata."""

    name: str
    version: str
    environment: str
    supported_engines: List[str] = Field(
        default_factory=lambda: ["vLLM", "SGLang", "TensorRT-LLM"]
    )
    hardware: HardwareInfo
