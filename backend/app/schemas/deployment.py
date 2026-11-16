"""Pydantic Schemas for Deployment Lifecycle and Endpoint Management."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from backend.app.schemas.model import ModelResponse


class DeploymentBase(BaseModel):
    """Base schema for serving endpoints."""

    name: str = Field(..., min_length=1, max_length=128, description="Unique human-readable deployment name")
    model_id: str = Field(..., min_length=36, max_length=36, description="Target registered Model UUID")
    engine: str = Field(default="vLLM", max_length=32, description="Inference engine backend (vLLM, SGLang, TensorRT-LLM)")
    tensor_parallel: int = Field(default=1, ge=1, le=8, description="Tensor parallelism GPU shard count")
    port: int = Field(..., ge=1024, le=65535, description="Network port allocated for the serving engine instance")
    max_model_len: int = Field(default=8192, ge=512, le=131072, description="Maximum sequence length configured on engine")
    gpu_type: str = Field(default="Auto-detect", max_length=128, description="Target GPU accelerator type")
    replicas: int = Field(default=1, ge=0, le=16, description="Serving worker replica count")
    base_url: Optional[str] = Field(default=None, max_length=255, description="Explicit HTTP base URL for endpoint")


class DeploymentCreate(DeploymentBase):
    """Payload schema for launching or registering a deployment endpoint."""

    pass


class DeploymentUpdate(BaseModel):
    """Payload schema for updating a deployment configuration or runtime status."""

    name: Optional[str] = Field(default=None, min_length=1, max_length=128)
    status: Optional[str] = Field(default=None, max_length=32, description="Operational status: running, stopped, starting, failed")
    replicas: Optional[int] = Field(default=None, ge=0, le=16)
    port: Optional[int] = Field(default=None, ge=1024, le=65535)
    tensor_parallel: Optional[int] = Field(default=None, ge=1, le=8)
    kv_cache_usage: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    qps: Optional[float] = Field(default=None, ge=0.0)
    base_url: Optional[str] = Field(default=None, max_length=255)


class DeploymentResponse(DeploymentBase):
    """Response schema for deployment endpoints with live telemetry."""

    id: str = Field(..., description="Unique UUID identifier")
    kv_cache_usage: float = Field(default=0.0, description="Real-time KV cache allocation percentage")
    qps: float = Field(default=0.0, description="Real-time queries per second")
    status: str = Field(default="stopped", description="Current lifecycle state")
    created_at: datetime
    updated_at: datetime
    model: Optional[ModelResponse] = None

    model_config = ConfigDict(from_attributes=True)


class DeploymentListResponse(BaseModel):
    """Paginated list response for deployments."""

    items: list[DeploymentResponse]
    total: int
    skip: int
    limit: int
