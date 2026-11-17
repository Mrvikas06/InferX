"""Autoscaling and Cluster Management Pydantic Schemas."""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field


class ScalingPolicyBase(BaseModel):
    """Base fields for autoscaling policy."""
    min_replicas: int = Field(default=1, ge=1, le=50, description="Minimum replica count")
    max_replicas: int = Field(default=5, ge=1, le=100, description="Maximum replica count")
    target_metric: Literal["qps", "latency_ms", "gpu_util", "queue_depth"] = Field(
        default="qps", description="Target metric for autoscale trigger"
    )
    target_value: float = Field(default=50.0, gt=0, description="Target value for metric")
    scale_up_cooldown: int = Field(
        default=60, ge=0, description="Cooldown seconds after scaling up"
    )
    scale_down_cooldown: int = Field(
        default=180, ge=0, description="Cooldown seconds after scaling down"
    )
    is_enabled: bool = Field(default=True, description="Whether autoscaler is active")


class ScalingPolicyCreate(ScalingPolicyBase):
    """Payload to create or set an autoscaling policy."""
    pass


class ScalingPolicyUpdate(BaseModel):
    """Payload to partially update an autoscaling policy."""
    min_replicas: Optional[int] = Field(default=None, ge=1, le=50)
    max_replicas: Optional[int] = Field(default=None, ge=1, le=100)
    target_metric: Optional[Literal["qps", "latency_ms", "gpu_util", "queue_depth"]] = None
    target_value: Optional[float] = Field(default=None, gt=0)
    scale_up_cooldown: Optional[int] = Field(default=None, ge=0)
    scale_down_cooldown: Optional[int] = Field(default=None, ge=0)
    is_enabled: Optional[bool] = None


class ScalingPolicyResponse(ScalingPolicyBase):
    """Response schema for autoscaling policy."""
    id: str
    deployment_id: str
    last_scale_at: Optional[datetime] = None
    last_scale_action: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReplicaInfo(BaseModel):
    """Runtime status of an individual model serving worker instance."""
    replica_id: str
    deployment_id: str
    endpoint_url: str
    port: int
    status: Literal["healthy", "unhealthy", "starting", "draining", "stopped"]
    active_requests: int = 0
    total_requests: int = 0
    error_count: int = 0
    avg_latency_ms: float = 0.0
    last_heartbeat: datetime
    uptime_seconds: float = 0.0


class ScaleRequest(BaseModel):
    """Manual scaling request payload."""
    replicas: int = Field(ge=1, le=50, description="Target number of replica workers")


class ScaleResponse(BaseModel):
    """Response returned upon scaling a deployment."""
    deployment_id: str
    previous_replicas: int
    desired_replicas: int
    current_replicas: int
    replicas: List[ReplicaInfo]
    message: str


class AutoscaleEvaluationResponse(BaseModel):
    """Result of an autoscaling evaluation pass."""
    deployment_id: str
    action: Literal["scale_up", "scale_down", "no_op", "cooldown", "disabled"]
    current_replicas: int
    recommended_replicas: int
    target_metric: str
    current_metric_value: float
    target_metric_value: float
    reason: str
    cooldown_remaining_seconds: float = 0.0


class ClusterDeploymentSummary(BaseModel):
    """Summary of a deployment's cluster presence."""
    deployment_id: str
    deployment_name: str
    model_repo_id: str
    status: str
    replicas_count: int
    healthy_replicas: int
    active_inflight_requests: int
    total_requests_served: int
    avg_latency_ms: float
    autoscaling_enabled: bool


class ClusterOverviewResponse(BaseModel):
    """Cluster-wide overview of worker instances, routing, and capacity."""
    total_deployments: int
    total_replicas: int
    healthy_replicas: int
    unhealthy_replicas: int
    total_active_requests: int
    total_requests_served: int
    routing_strategy: str
    deployments: List[ClusterDeploymentSummary]
