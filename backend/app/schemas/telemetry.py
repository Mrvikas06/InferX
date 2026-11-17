"""Telemetry, GPU Hardware Metrics, and Time-Series Schemas."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class GPUStats(BaseModel):
    """Real-time hardware statistics for a physical or simulated GPU."""

    index: int = Field(..., description="GPU device index (0, 1, ...)")
    name: str = Field(..., description="Device commercial model name")
    driver_version: Optional[str] = Field(None, description="Installed NVIDIA display driver version")
    memory_total_mb: float = Field(..., description="Total installed VRAM in megabytes")
    memory_used_mb: float = Field(..., description="Currently allocated VRAM in megabytes")
    memory_free_mb: float = Field(..., description="Available unallocated VRAM in megabytes")
    memory_utilization_pct: float = Field(..., description="Percentage of VRAM in active use")
    gpu_utilization_pct: float = Field(..., description="Percentage of GPU compute cores active")
    temperature_c: Optional[float] = Field(None, description="Die temperature in Celsius")
    power_draw_w: Optional[float] = Field(None, description="Current power draw in Watts")
    power_limit_w: Optional[float] = Field(None, description="Maximum TDP power envelope in Watts")
    is_simulated: bool = Field(False, description="Whether metrics are generated via software simulation")


class SystemResourceStats(BaseModel):
    """Host machine compute, RAM, and disk utilization statistics."""

    cpu_utilization_pct: float
    cpu_count: int
    ram_total_gb: float
    ram_used_gb: float
    ram_utilization_pct: float
    disk_total_gb: float
    disk_used_gb: float
    disk_utilization_pct: float


class InferenceMetricsSnapshot(BaseModel):
    """Instantaneous throughput, latency percentiles, and serving health."""

    timestamp: str
    qps: float
    total_requests: int
    tokens_per_second: float
    avg_ttft_ms: float
    latency_p50_ms: float
    latency_p95_ms: float
    latency_p99_ms: float
    kv_cache_usage_pct: float
    active_deployments: int


class HistoricalMetricPoint(BaseModel):
    """Single discrete historical snapshot point for timeseries graphing."""

    timestamp: str
    qps: float
    gpu_utilization_pct: float
    vram_used_mb: float
    latency_p95_ms: float
    tokens_per_sec: float


class TelemetryOverviewResponse(BaseModel):
    """Aggregated real-time observability telemetry payload."""

    gpus: List[GPUStats]
    system: SystemResourceStats
    inference: InferenceMetricsSnapshot
