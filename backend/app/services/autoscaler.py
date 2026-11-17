"""Autoscaler Service and Policy Evaluation Engine for InferX."""

from datetime import datetime, timezone
import logging
import math
from typing import Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

try:
    from backend.app.models.deployment import Deployment
    from backend.app.models.scaling import ScalingPolicy
    from backend.app.repositories.deployment_repository import deployment_repository
    from backend.app.repositories.scaling_repository import scaling_repository
    from backend.app.schemas.scaling import AutoscaleEvaluationResponse
    from backend.app.services.gpu_monitor import get_gpu_telemetry
    from backend.app.services.load_balancer import load_balancer
    from backend.app.services.telemetry_service import telemetry_service
except (ImportError, ModuleNotFoundError):
    from app.models.deployment import Deployment
    from app.models.scaling import ScalingPolicy
    from app.repositories.deployment_repository import deployment_repository
    from app.repositories.scaling_repository import scaling_repository
    from app.schemas.scaling import AutoscaleEvaluationResponse
    from app.services.gpu_monitor import get_gpu_telemetry
    from app.services.load_balancer import load_balancer
    from app.services.telemetry_service import telemetry_service

logger = logging.getLogger("inferx.autoscaler")


class AutoscalerService:
    """Evaluates metrics against scaling policies and executes auto-rebalancing."""

    async def evaluate_deployment(
        self,
        db: AsyncSession,
        deployment: Deployment,
        policy: Optional[ScalingPolicy] = None,
        apply_scaling: bool = False,
    ) -> AutoscaleEvaluationResponse:
        """
        Evaluate scaling conditions for a given deployment and optionally apply changes.
        """
        if not policy:
            policy = await scaling_repository.get_by_deployment_id(db, deployment.id)

        current_replicas = max(1, deployment.replicas)

        if not policy or not policy.is_enabled:
            return AutoscaleEvaluationResponse(
                deployment_id=deployment.id,
                action="disabled",
                current_replicas=current_replicas,
                recommended_replicas=current_replicas,
                target_metric=policy.target_metric if policy else "none",
                current_metric_value=0.0,
                target_metric_value=policy.target_value if policy else 0.0,
                reason="Autoscaling is disabled or no policy configured",
                cooldown_remaining_seconds=0.0,
            )

        # 1. Fetch current metric value based on policy target_metric
        metric_val = await self._fetch_metric_value(deployment, policy.target_metric)

        # 2. Compute recommended replica target
        target_replicas = self._calculate_target_replicas(
            current_replicas=current_replicas,
            metric_val=metric_val,
            target_val=policy.target_value,
            metric_type=policy.target_metric,
            min_reps=policy.min_replicas,
            max_reps=policy.max_replicas,
        )

        now = datetime.now(timezone.utc)
        cooldown_remaining = 0.0

        if target_replicas > current_replicas:
            # Check scale up cooldown
            if policy.last_scale_at:
                elapsed = (now - policy.last_scale_at).total_seconds()
                if elapsed < policy.scale_up_cooldown:
                    cooldown_remaining = round(policy.scale_up_cooldown - elapsed, 1)
                    return AutoscaleEvaluationResponse(
                        deployment_id=deployment.id,
                        action="cooldown",
                        current_replicas=current_replicas,
                        recommended_replicas=target_replicas,
                        target_metric=policy.target_metric,
                        current_metric_value=metric_val,
                        target_metric_value=policy.target_value,
                        reason=f"Scale up needed ({target_replicas} reps) but in cooldown window",
                        cooldown_remaining_seconds=cooldown_remaining,
                    )

            action = "scale_up"
            reason = (
                f"Metric {policy.target_metric} ({metric_val}) exceeded threshold "
                f"({policy.target_value}). Scaling up from {current_replicas} to {target_replicas}."
            )

        elif target_replicas < current_replicas:
            # Check scale down cooldown
            if policy.last_scale_at:
                elapsed = (now - policy.last_scale_at).total_seconds()
                if elapsed < policy.scale_down_cooldown:
                    cooldown_remaining = round(policy.scale_down_cooldown - elapsed, 1)
                    return AutoscaleEvaluationResponse(
                        deployment_id=deployment.id,
                        action="cooldown",
                        current_replicas=current_replicas,
                        recommended_replicas=target_replicas,
                        target_metric=policy.target_metric,
                        current_metric_value=metric_val,
                        target_metric_value=policy.target_value,
                        reason=f"Scale down suggested ({target_replicas} reps) but in cooldown window",
                        cooldown_remaining_seconds=cooldown_remaining,
                    )

            action = "scale_down"
            reason = (
                f"Metric {policy.target_metric} ({metric_val}) is below target "
                f"({policy.target_value}). Scaling down from {current_replicas} to {target_replicas}."
            )

        else:
            action = "no_op"
            reason = (
                f"Metric {policy.target_metric} ({metric_val}) is balanced. "
                f"Replicas remain at {current_replicas}."
            )

        # 3. Apply scaling action if requested and not no_op
        if apply_scaling and action in ("scale_up", "scale_down"):
            await self._apply_scale(
                db=db,
                deployment=deployment,
                policy=policy,
                target_replicas=target_replicas,
                action_desc=f"{action}_to_{target_replicas}",
            )

        return AutoscaleEvaluationResponse(
            deployment_id=deployment.id,
            action=action,
            current_replicas=current_replicas,
            recommended_replicas=target_replicas,
            target_metric=policy.target_metric,
            current_metric_value=metric_val,
            target_metric_value=policy.target_value,
            reason=reason,
            cooldown_remaining_seconds=0.0,
        )

    async def _fetch_metric_value(self, deployment: Deployment, metric_type: str) -> float:
        """Query real or simulated metric telemetry."""
        if metric_type == "qps":
            # If deployment has explicit qps set > 0, respect it, else check live snapshot
            if deployment.qps > 0:
                return float(deployment.qps)
            snapshot = telemetry_service.get_live_inference_snapshot(active_deployments_count=1)
            return float(snapshot.qps)

        elif metric_type == "latency_ms":
            # Check replica moving average or P95 from live snapshot
            pool = load_balancer.get_replicas(deployment.id)
            if pool:
                avg = sum(r.avg_latency_ms for r in pool) / len(pool)
                if avg > 0:
                    return round(avg, 2)
            snapshot = telemetry_service.get_live_inference_snapshot(active_deployments_count=1)
            return float(snapshot.latency_p95_ms)

        elif metric_type == "queue_depth":
            # Total active inflight requests across all replicas of this deployment
            pool = load_balancer.get_replicas(deployment.id)
            return float(sum(r.active_requests for r in pool))

        elif metric_type == "gpu_util":
            # Check physical GPU status or simulation
            gpus = get_gpu_telemetry()
            if gpus:
                return float(gpus[0].gpu_utilization_pct)
            return 0.0

        return 0.0

    def _calculate_target_replicas(
        self,
        current_replicas: int,
        metric_val: float,
        target_val: float,
        metric_type: str,
        min_reps: int,
        max_reps: int,
    ) -> int:
        """Calculate desired replica count clamped by [min_reps, max_reps]."""
        if target_val <= 0:
            return current_replicas

        if metric_type in ("qps", "queue_depth"):
            # Target is capacity per replica; total required = ceil(total_metric / target_val)
            if metric_val <= 0:
                desired = min_reps
            else:
                desired = math.ceil(metric_val / target_val)
        elif metric_type == "latency_ms":
            # If latency exceeds 1.25x target, scale up; if latency < 0.5x target, scale down
            if metric_val > target_val * 1.25:
                desired = current_replicas + 1
            elif metric_val < target_val * 0.5 and current_replicas > min_reps:
                desired = current_replicas - 1
            else:
                desired = current_replicas
        elif metric_type == "gpu_util":
            # If GPU util > 85%, scale out; if < 30%, scale in
            if metric_val > target_val:
                desired = current_replicas + 1
            elif metric_val < target_val * 0.4 and current_replicas > min_reps:
                desired = current_replicas - 1
            else:
                desired = current_replicas
        else:
            desired = current_replicas

        # Clamp between min and max bounds
        return max(min_reps, min(max_reps, desired))

    async def _apply_scale(
        self,
        db: AsyncSession,
        deployment: Deployment,
        policy: ScalingPolicy,
        target_replicas: int,
        action_desc: str,
    ) -> None:
        """Apply scaling to deployment record, replica pool, and policy audit."""
        logger.info(
            "Applying autoscale for %s: %d -> %d (%s)",
            deployment.name,
            deployment.replicas,
            target_replicas,
            action_desc,
        )
        deployment.replicas = target_replicas
        await db.commit()
        await db.refresh(deployment)

        # Sync load balancer pool
        load_balancer.sync_deployment_replicas(
            deployment_id=deployment.id,
            base_port=deployment.port,
            target_replicas=target_replicas,
            is_running=(deployment.status == "running"),
        )

        # Update policy last scale record
        await scaling_repository.record_scale_event(
            db=db,
            deployment_id=deployment.id,
            action=action_desc,
        )


autoscaler = AutoscalerService()
