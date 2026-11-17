"""Pydantic Schemas for Inference Benchmark and Load Testing."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class BenchmarkBase(BaseModel):
    """Base schema for benchmark test execution request."""

    name: str = Field(..., min_length=1, max_length=128, description="Human-readable benchmark name")
    deployment_id: str = Field(..., min_length=36, max_length=36, description="Target Deployment UUID")
    concurrency: int = Field(default=16, ge=1, le=256, description="Simultaneous concurrent request workers")
    num_prompts: int = Field(default=64, ge=1, le=2000, description="Total synthetic prompts to dispatch")
    input_tokens: int = Field(default=256, ge=16, le=8192, description="Target prompt length in tokens")
    output_tokens: int = Field(default=128, ge=8, le=4096, description="Maximum generation tokens per request")


class BenchmarkCreate(BenchmarkBase):
    """Payload schema to initiate a new benchmark load test."""

    pass


class BenchmarkResponse(BaseModel):
    """Full benchmark report schema with latency distribution and throughput."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    deployment_id: str
    model_id: Optional[str] = None
    status: str
    engine: str
    concurrency: int
    num_prompts: int
    input_tokens: int
    output_tokens: int

    # Throughput & Latency Metrics
    rps: float
    tokens_per_sec: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    p50_ttft_ms: float
    p99_ttft_ms: float
    mean_tpot_ms: float
    vram_peak_gb: float
    error_count: int

    results_json: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_name: Optional[str] = None
    deployment_name: Optional[str] = None


class BenchmarkListResponse(BaseModel):
    """Paginated benchmark history list."""

    total: int
    items: List[BenchmarkResponse]
