"""Cluster Scaling, Load Balancing, and Autoscaler API Router for InferX."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

try:
    from backend.app.api.deps import AuthContext, get_optional_auth_context
    from backend.app.core.security import has_sufficient_role
    from backend.app.db.session import get_db
    from backend.app.repositories.deployment_repository import deployment_repository
    from backend.app.repositories.scaling_repository import scaling_repository
    from backend.app.schemas.scaling import (
        AutoscaleEvaluationResponse,
        ClusterDeploymentSummary,
        ClusterOverviewResponse,
        ReplicaInfo,
        ScaleRequest,
        ScaleResponse,
        ScalingPolicyCreate,
        ScalingPolicyResponse,
        ScalingPolicyUpdate,
    )
    from backend.app.services.autoscaler import autoscaler
    from backend.app.services.load_balancer import RoutingStrategy, load_balancer
except (ImportError, ModuleNotFoundError):
    from app.api.deps import AuthContext, get_optional_auth_context
    from app.core.security import has_sufficient_role
    from app.db.session import get_db
    from app.repositories.deployment_repository import deployment_repository
    from app.repositories.scaling_repository import scaling_repository
    from app.schemas.scaling import (
        AutoscaleEvaluationResponse,
        ClusterDeploymentSummary,
        ClusterOverviewResponse,
        ReplicaInfo,
        ScaleRequest,
        ScaleResponse,
        ScalingPolicyCreate,
        ScalingPolicyResponse,
        ScalingPolicyUpdate,
    )
    from app.services.autoscaler import autoscaler
    from app.services.load_balancer import RoutingStrategy, load_balancer

router = APIRouter(prefix="/cluster", tags=["Cluster & Autoscaling"])


class StrategyUpdateRequest(BaseModel):
    strategy: RoutingStrategy


@router.get("/overview", response_model=ClusterOverviewResponse)
async def get_cluster_overview(
    db: AsyncSession = Depends(get_db),
    auth: Optional[AuthContext] = Depends(get_optional_auth_context),
) -> ClusterOverviewResponse:
    """Fetch aggregate cluster telemetry and deployment replica summaries."""
    deployments = await deployment_repository.list_deployments(db, limit=100)
    summaries: List[ClusterDeploymentSummary] = []

    for dep in deployments:
        # Sync replica registry to ensure accuracy
        pool = load_balancer.sync_deployment_replicas(
            deployment_id=dep.id,
            base_port=dep.port,
            target_replicas=max(1, dep.replicas),
            is_running=(dep.status == "running"),
        )
        healthy = sum(1 for r in pool if r.status == "healthy")
        active_reqs = sum(r.active_requests for r in pool)
        total_reqs = sum(r.total_requests for r in pool)
        avg_lat = (
            round(sum(r.avg_latency_ms for r in pool) / len(pool), 2)
            if pool and any(r.avg_latency_ms > 0 for r in pool)
            else 0.0
        )
        policy = await scaling_repository.get_by_deployment_id(db, dep.id)

        summaries.append(
            ClusterDeploymentSummary(
                deployment_id=dep.id,
                deployment_name=dep.name,
                model_repo_id=dep.model.repo_id if dep.model else "unknown",
                status=dep.status,
                replicas_count=dep.replicas,
                healthy_replicas=healthy,
                active_inflight_requests=active_reqs,
                total_requests_served=total_reqs,
                avg_latency_ms=avg_lat,
                autoscaling_enabled=bool(policy and policy.is_enabled),
            )
        )

    stats = load_balancer.get_cluster_stats()
    return ClusterOverviewResponse(
        total_deployments=len(deployments),
        total_replicas=stats["total_replicas"],
        healthy_replicas=stats["healthy_replicas"],
        unhealthy_replicas=stats["unhealthy_replicas"],
        total_active_requests=stats["total_active_requests"],
        total_requests_served=stats["total_requests_served"],
        routing_strategy=stats["routing_strategy"],
        deployments=summaries,
    )


@router.post("/deployments/{deployment_id}/scale", response_model=ScaleResponse)
async def scale_deployment(
    deployment_id: str,
    payload: ScaleRequest,
    db: AsyncSession = Depends(get_db),
    auth: Optional[AuthContext] = Depends(get_optional_auth_context),
) -> ScaleResponse:
    """Manually scale the number of replica instances for a deployment."""
    if auth and not has_sufficient_role(auth.role, "operator"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operator role required")

    deployment = await deployment_repository.get_by_id(db, deployment_id)
    if not deployment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deployment not found")

    prev_replicas = deployment.replicas
    deployment.replicas = payload.replicas
    await db.commit()
    await db.refresh(deployment)

    # Sync load balancer pool
    pool = load_balancer.sync_deployment_replicas(
        deployment_id=deployment.id,
        base_port=deployment.port,
        target_replicas=payload.replicas,
        is_running=(deployment.status == "running"),
    )

    replicas_info = [ReplicaInfo(**r.to_dict()) for r in pool]

    return ScaleResponse(
        deployment_id=deployment.id,
        previous_replicas=prev_replicas,
        desired_replicas=payload.replicas,
        current_replicas=len(pool),
        replicas=replicas_info,
        message=f"Deployment successfully scaled from {prev_replicas} to {payload.replicas} replicas",
    )


@router.get("/deployments/{deployment_id}/replicas", response_model=List[ReplicaInfo])
async def list_deployment_replicas(
    deployment_id: str,
    db: AsyncSession = Depends(get_db),
    auth: Optional[AuthContext] = Depends(get_optional_auth_context),
) -> List[ReplicaInfo]:
    """List all replica worker instances and runtime telemetry for a deployment."""
    deployment = await deployment_repository.get_by_id(db, deployment_id)
    if not deployment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deployment not found")

    pool = load_balancer.sync_deployment_replicas(
        deployment_id=deployment.id,
        base_port=deployment.port,
        target_replicas=max(1, deployment.replicas),
        is_running=(deployment.status == "running"),
    )
    return [ReplicaInfo(**r.to_dict()) for r in pool]


@router.get(
    "/deployments/{deployment_id}/scaling-policy",
    response_model=Optional[ScalingPolicyResponse],
)
async def get_scaling_policy(
    deployment_id: str,
    db: AsyncSession = Depends(get_db),
    auth: Optional[AuthContext] = Depends(get_optional_auth_context),
) -> Optional[ScalingPolicyResponse]:
    """Retrieve the autoscaling policy configured for a deployment."""
    deployment = await deployment_repository.get_by_id(db, deployment_id)
    if not deployment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deployment not found")

    policy = await scaling_repository.get_by_deployment_id(db, deployment_id)
    if not policy:
        return None
    return ScalingPolicyResponse.model_validate(policy)


@router.put("/deployments/{deployment_id}/scaling-policy", response_model=ScalingPolicyResponse)
async def set_scaling_policy(
    deployment_id: str,
    payload: ScalingPolicyCreate,
    db: AsyncSession = Depends(get_db),
    auth: Optional[AuthContext] = Depends(get_optional_auth_context),
) -> ScalingPolicyResponse:
    """Create or update autoscaling policy for a deployment."""
    if auth and not has_sufficient_role(auth.role, "operator"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operator role required")

    deployment = await deployment_repository.get_by_id(db, deployment_id)
    if not deployment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deployment not found")

    if payload.min_replicas > payload.max_replicas:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="min_replicas cannot exceed max_replicas",
        )

    policy = await scaling_repository.create_or_update_policy(db, deployment_id, payload)
    return ScalingPolicyResponse.model_validate(policy)


@router.post(
    "/deployments/{deployment_id}/autoscale/evaluate",
    response_model=AutoscaleEvaluationResponse,
)
async def evaluate_autoscaler(
    deployment_id: str,
    apply: bool = Query(default=True, description="Whether to apply the scaling recommendation"),
    db: AsyncSession = Depends(get_db),
    auth: Optional[AuthContext] = Depends(get_optional_auth_context),
) -> AutoscaleEvaluationResponse:
    """Trigger an immediate autoscaling evaluation pass for a deployment."""
    if auth and not has_sufficient_role(auth.role, "operator"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operator role required")

    deployment = await deployment_repository.get_by_id(db, deployment_id)
    if not deployment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deployment not found")

    eval_result = await autoscaler.evaluate_deployment(
        db=db,
        deployment=deployment,
        apply_scaling=apply,
    )
    return eval_result


@router.post("/strategy")
async def update_routing_strategy(
    payload: StrategyUpdateRequest,
    auth: Optional[AuthContext] = Depends(get_optional_auth_context),
) -> dict:
    """Update global cluster load balancing routing strategy."""
    if auth and not has_sufficient_role(auth.role, "operator"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operator role required")

    load_balancer.default_strategy = payload.strategy
    return {
        "status": "updated",
        "routing_strategy": load_balancer.default_strategy,
    }
    """Update global cluster load balancing routing strategy."""
    load_balancer.default_strategy = payload.strategy
    return {
        "status": "updated",
        "routing_strategy": load_balancer.default_strategy,
    }
