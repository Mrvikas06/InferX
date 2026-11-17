"""Load Balancer, Replica Registry, and Intelligent Routing Engine for InferX."""

import asyncio
from datetime import datetime, timezone
import logging
import random
import time
from typing import Dict, List, Literal, Optional

logger = logging.getLogger("inferx.load_balancer")

RoutingStrategy = Literal["least_connections", "round_robin", "weighted_latency", "random"]


class ReplicaInstance:
    """Represents an active or drained worker instance serving a deployment."""

    def __init__(
        self,
        deployment_id: str,
        port: int,
        status: Literal["healthy", "unhealthy", "starting", "draining", "stopped"] = "healthy",
    ):
        self.deployment_id = deployment_id
        self.port = port
        self.replica_id = f"rep-{deployment_id[:8]}-{port}"
        self.endpoint_url = f"http://127.0.0.1:{port}"
        self.status = status
        self.active_requests: int = 0
        self.total_requests: int = 0
        self.error_count: int = 0
        self.avg_latency_ms: float = 0.0
        self.last_heartbeat: datetime = datetime.now(timezone.utc)
        self.started_at: datetime = datetime.now(timezone.utc)

    @property
    def uptime_seconds(self) -> float:
        """Calculate instance uptime in seconds."""
        return (datetime.now(timezone.utc) - self.started_at).total_seconds()

    def record_request_start(self) -> None:
        """Increment inflight active request counter."""
        self.active_requests += 1
        self.total_requests += 1
        self.last_heartbeat = datetime.now(timezone.utc)

    def record_request_end(self, latency_ms: float, success: bool = True) -> None:
        """Decrement active request counter and update rolling latency."""
        self.active_requests = max(0, self.active_requests - 1)
        self.last_heartbeat = datetime.now(timezone.utc)

        if success:
            self.error_count = 0
            if self.status == "unhealthy":
                self.status = "healthy"

            # Exponential moving average (alpha = 0.2)
            if self.avg_latency_ms == 0.0:
                self.avg_latency_ms = latency_ms
            else:
                self.avg_latency_ms = round((0.8 * self.avg_latency_ms) + (0.2 * latency_ms), 2)
        else:
            self.error_count += 1
            if self.error_count >= 3:
                logger.warning(
                    "Replica %s marked unhealthy after %d consecutive errors",
                    self.replica_id,
                    self.error_count,
                )
                self.status = "unhealthy"

    def to_dict(self) -> Dict:
        """Serialize replica telemetry."""
        return {
            "replica_id": self.replica_id,
            "deployment_id": self.deployment_id,
            "endpoint_url": self.endpoint_url,
            "port": self.port,
            "status": self.status,
            "active_requests": self.active_requests,
            "total_requests": self.total_requests,
            "error_count": self.error_count,
            "avg_latency_ms": self.avg_latency_ms,
            "last_heartbeat": self.last_heartbeat,
            "uptime_seconds": round(self.uptime_seconds, 2),
        }


class LoadBalancer:
    """Manages replica pools and routes inference traffic across worker instances."""

    def __init__(self, default_strategy: RoutingStrategy = "least_connections"):
        self.default_strategy: RoutingStrategy = default_strategy
        # deployment_id -> list of ReplicaInstance
        self._pools: Dict[str, List[ReplicaInstance]] = {}
        # deployment_id -> round-robin index counter
        self._rr_counters: Dict[str, int] = {}
        self._lock = asyncio.Lock()

    def sync_deployment_replicas(
        self,
        deployment_id: str,
        base_port: int,
        target_replicas: int,
        is_running: bool = True,
    ) -> List[ReplicaInstance]:
        """
        Synchronize the worker pool for a deployment to match target_replicas.
        Allocates ports base_port, base_port + 1, ...
        """
        pool = self._pools.setdefault(deployment_id, [])
        initial_status: Literal["healthy", "stopped"] = "healthy" if is_running else "stopped"

        # Scale down: drain or remove excess replicas from the end
        if len(pool) > target_replicas:
            excess = len(pool) - target_replicas
            logger.info("Scaling down deployment %s: removing %d replicas", deployment_id, excess)
            pool = pool[:target_replicas]
            self._pools[deployment_id] = pool

        # Scale up: instantiate new replica objects with sequential ports
        elif len(pool) < target_replicas:
            existing_ports = {r.port for r in pool}
            needed = target_replicas - len(pool)
            port_candidate = base_port

            for _ in range(needed):
                while port_candidate in existing_ports:
                    port_candidate += 1
                new_replica = ReplicaInstance(
                    deployment_id=deployment_id,
                    port=port_candidate,
                    status=initial_status,
                )
                pool.append(new_replica)
                existing_ports.add(port_candidate)
                port_candidate += 1

            logger.info("Scaled up deployment %s to %d replicas", deployment_id, len(pool))

        # Update status if changed (e.g. deployment started or stopped)
        for rep in pool:
            if not is_running and rep.status != "stopped":
                rep.status = "stopped"
            elif is_running and rep.status == "stopped":
                rep.status = "healthy"

        return pool

    def get_replicas(self, deployment_id: str) -> List[ReplicaInstance]:
        """Return list of replicas for a deployment."""
        return list(self._pools.get(deployment_id, []))

    def acquire_replica(
        self,
        deployment_id: str,
        strategy: Optional[RoutingStrategy] = None,
    ) -> Optional[ReplicaInstance]:
        """
        Select the best healthy replica using the requested routing strategy.
        Atomically records request start.
        """
        pool = self._pools.get(deployment_id, [])
        if not pool:
            return None

        # Filter for eligible healthy replicas
        healthy_candidates = [r for r in pool if r.status == "healthy"]
        if not healthy_candidates:
            # If all are temporarily unhealthy, fallback to any available instance
            healthy_candidates = pool

        active_strategy = strategy or self.default_strategy
        selected: Optional[ReplicaInstance] = None

        if active_strategy == "least_connections":
            # Select candidate with lowest inflight requests; break ties by avg latency
            selected = min(
                healthy_candidates,
                key=lambda r: (r.active_requests, r.avg_latency_ms),
            )

        elif active_strategy == "round_robin":
            idx = self._rr_counters.get(deployment_id, 0)
            selected = healthy_candidates[idx % len(healthy_candidates)]
            self._rr_counters[deployment_id] = (idx + 1) % len(healthy_candidates)

        elif active_strategy == "weighted_latency":
            # Select candidate with lowest average latency
            selected = min(healthy_candidates, key=lambda r: r.avg_latency_ms)

        elif active_strategy == "random":
            selected = random.choice(healthy_candidates)

        else:
            selected = healthy_candidates[0]

        if selected:
            selected.record_request_start()

        return selected

    def release_replica(
        self,
        replica: ReplicaInstance,
        latency_ms: float,
        success: bool = True,
    ) -> None:
        """Release active request and update telemetry stats."""
        replica.record_request_end(latency_ms, success)

    def mark_replica_status(
        self,
        deployment_id: str,
        replica_id: str,
        status: Literal["healthy", "unhealthy", "starting", "draining", "stopped"],
    ) -> Optional[ReplicaInstance]:
        """Manually override a replica status."""
        pool = self._pools.get(deployment_id, [])
        for r in pool:
            if r.replica_id == replica_id:
                r.status = status
                if status == "healthy":
                    r.error_count = 0
                return r
        return None

    def unregister_deployment(self, deployment_id: str) -> None:
        """Remove all replica instances for a removed deployment."""
        self._pools.pop(deployment_id, None)
        self._rr_counters.pop(deployment_id, None)

    def get_cluster_stats(self) -> Dict:
        """Compute aggregate cluster stats across all replica pools."""
        total_replicas = 0
        healthy_replicas = 0
        unhealthy_replicas = 0
        total_active_requests = 0
        total_requests_served = 0

        for pool in self._pools.values():
            for r in pool:
                total_replicas += 1
                if r.status == "healthy":
                    healthy_replicas += 1
                elif r.status in ("unhealthy", "stopped"):
                    unhealthy_replicas += 1
                total_active_requests += r.active_requests
                total_requests_served += r.total_requests

        return {
            "total_deployments": len(self._pools),
            "total_replicas": total_replicas,
            "healthy_replicas": healthy_replicas,
            "unhealthy_replicas": unhealthy_replicas,
            "total_active_requests": total_active_requests,
            "total_requests_served": total_requests_served,
            "routing_strategy": self.default_strategy,
        }


# Global LoadBalancer Singleton
load_balancer = LoadBalancer()
