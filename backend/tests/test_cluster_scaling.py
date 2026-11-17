"""Integration and Unit Tests for Cluster Scaling, Load Balancer, and Autoscaler."""

from datetime import datetime, timedelta, timezone
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.deployment import Deployment
from backend.app.models.model import Model
from backend.app.models.scaling import ScalingPolicy
from backend.app.models.user import User
from backend.app.services.autoscaler import autoscaler
from backend.app.services.load_balancer import LoadBalancer, ReplicaInstance, load_balancer


@pytest.mark.asyncio
async def test_load_balancer_routing_strategies():
    """Verify routing algorithms: least_connections, round_robin, weighted_latency."""
    lb = LoadBalancer()
    dep_id = "test-dep-lb-1"
    base_port = 8100

    # Sync to 3 replicas
    pool = lb.sync_deployment_replicas(dep_id, base_port, target_replicas=3, is_running=True)
    assert len(pool) == 3
    assert [r.port for r in pool] == [8100, 8101, 8102]

    # Test round_robin
    r1 = lb.acquire_replica(dep_id, strategy="round_robin")
    r2 = lb.acquire_replica(dep_id, strategy="round_robin")
    r3 = lb.acquire_replica(dep_id, strategy="round_robin")
    assert r1 is not None and r2 is not None and r3 is not None
    assert {r1.port, r2.port, r3.port} == {8100, 8101, 8102}

    # Release them
    lb.release_replica(r1, latency_ms=50.0, success=True)
    lb.release_replica(r2, latency_ms=10.0, success=True)
    lb.release_replica(r3, latency_ms=80.0, success=True)

    # Test least_connections: artificially increase active requests on two replicas
    pool[0].active_requests = 5
    pool[1].active_requests = 0  # should be selected
    pool[2].active_requests = 3
    selected = lb.acquire_replica(dep_id, strategy="least_connections")
    assert selected is not None
    assert selected.port == 8101
    lb.release_replica(selected, latency_ms=15.0, success=True)

    # Test weighted_latency: should pick replica with lowest avg_latency
    pool[0].active_requests = 0
    pool[1].active_requests = 0
    pool[2].active_requests = 0
    pool[0].avg_latency_ms = 120.0
    pool[1].avg_latency_ms = 12.0  # lowest latency
    pool[2].avg_latency_ms = 45.0
    selected_lat = lb.acquire_replica(dep_id, strategy="weighted_latency")
    assert selected_lat is not None
    assert selected_lat.port == 8101
    lb.release_replica(selected_lat, latency_ms=12.0, success=True)


@pytest.mark.asyncio
async def test_load_balancer_health_degradation_and_recovery():
    """Verify unhealthy degradation after consecutive failures and recovery."""
    lb = LoadBalancer()
    dep_id = "test-health-dep"
    pool = lb.sync_deployment_replicas(dep_id, 8200, target_replicas=1, is_running=True)
    rep = pool[0]

    # 1 fail: still healthy
    lb.release_replica(rep, latency_ms=0, success=False)
    assert rep.status == "healthy"
    assert rep.error_count == 1

    # 2 fails: still healthy
    lb.release_replica(rep, latency_ms=0, success=False)
    assert rep.status == "healthy"
    assert rep.error_count == 2

    # 3 fails: marks unhealthy
    lb.release_replica(rep, latency_ms=0, success=False)
    assert rep.status == "unhealthy"
    assert rep.error_count == 3

    # Success: recovers to healthy
    lb.release_replica(rep, latency_ms=35.0, success=True)
    assert rep.status == "healthy"
    assert rep.error_count == 0


@pytest.mark.asyncio
async def test_autoscaler_service_evaluation(db_session: AsyncSession):
    """Test autoscaler evaluation calculations and bounds clamping."""
    # Create test model and deployment
    model = Model(
        repo_id="test/autoscaler-model",
        name="Autoscaler Model",
        parameters="7B",
        precision="BF16",
        context_window=4096,
        is_downloaded=True,
    )
    db_session.add(model)
    await db_session.flush()

    deployment = Deployment(
        name="test-autoscale-dep",
        model_id=model.id,
        engine="vLLM",
        port=8300,
        replicas=2,
        status="running",
        qps=150.0,
    )
    db_session.add(deployment)
    await db_session.flush()

    # Create scaling policy targeting QPS = 50.0 per replica, max = 5
    policy = ScalingPolicy(
        deployment_id=deployment.id,
        min_replicas=1,
        max_replicas=5,
        target_metric="qps",
        target_value=50.0,
        scale_up_cooldown=60,
        scale_down_cooldown=180,
        is_enabled=True,
    )
    db_session.add(policy)
    await db_session.commit()

    # Evaluate: current QPS is 150.0, target is 50.0 -> desired = ceil(150/50) = 3
    result = await autoscaler.evaluate_deployment(
        db=db_session,
        deployment=deployment,
        policy=policy,
        apply_scaling=True,
    )
    assert result.action == "scale_up"
    assert result.recommended_replicas >= 3
    assert deployment.replicas == result.recommended_replicas

    # Immediate second evaluation should trigger cooldown
    result_cooldown = await autoscaler.evaluate_deployment(
        db=db_session,
        deployment=deployment,
        policy=policy,
        apply_scaling=False,
    )
    # Since cooldown was set by apply_scale, it should either be in cooldown or balanced
    assert result_cooldown.action in ("cooldown", "no_op")


@pytest.mark.asyncio
async def test_cluster_api_lifecycle(
    async_client: AsyncClient,
    db_session: AsyncSession,
):
    """Test full Cluster API: overview, scaling, replicas, and policy endpoints."""
    # 0. Register and obtain admin auth token
    await async_client.post(
        "/api/v1/auth/register",
        json={"email": "clusteradmin@inferx.ai", "password": "Password123!"},
    )
    login_resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "clusteradmin@inferx.ai", "password": "Password123!"},
    )
    admin_token = login_resp.json()["data"]["access_token"]
    admin_auth_headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Create Model and Deployment
    model = Model(
        repo_id="test/cluster-api-model",
        name="Cluster API Model",
        parameters="13B",
        precision="FP16",
        context_window=8192,
        is_downloaded=True,
    )
    db_session.add(model)
    await db_session.flush()

    deployment = Deployment(
        name="test-cluster-dep",
        model_id=model.id,
        engine="vLLM",
        port=8400,
        replicas=1,
        status="running",
    )
    db_session.add(deployment)
    await db_session.commit()
    await db_session.refresh(deployment)

    # 2. Get Cluster Overview
    resp_overview = await async_client.get(
        "/api/v1/cluster/overview",
        headers=admin_auth_headers,
    )
    assert resp_overview.status_code == 200
    data_overview = resp_overview.json()
    assert "total_deployments" in data_overview
    assert "total_replicas" in data_overview
    assert len(data_overview["deployments"]) >= 1

    # 3. Manually Scale Deployment to 3 replicas
    resp_scale = await async_client.post(
        f"/api/v1/cluster/deployments/{deployment.id}/scale",
        json={"replicas": 3},
        headers=admin_auth_headers,
    )
    assert resp_scale.status_code == 200
    scale_data = resp_scale.json()
    assert scale_data["desired_replicas"] == 3
    assert len(scale_data["replicas"]) == 3

    # 4. List replicas for deployment
    resp_reps = await async_client.get(
        f"/api/v1/cluster/deployments/{deployment.id}/replicas",
        headers=admin_auth_headers,
    )
    assert resp_reps.status_code == 200
    reps_data = resp_reps.json()
    assert len(reps_data) == 3
    assert reps_data[0]["port"] == 8400

    # 5. Set Autoscaling Policy
    policy_payload = {
        "min_replicas": 1,
        "max_replicas": 6,
        "target_metric": "qps",
        "target_value": 75.0,
        "scale_up_cooldown": 30,
        "scale_down_cooldown": 60,
        "is_enabled": True,
    }
    resp_policy = await async_client.put(
        f"/api/v1/cluster/deployments/{deployment.id}/scaling-policy",
        json=policy_payload,
        headers=admin_auth_headers,
    )
    assert resp_policy.status_code == 200
    policy_data = resp_policy.json()
    assert policy_data["max_replicas"] == 6
    assert policy_data["target_value"] == 75.0

    # 6. Fetch Autoscaling Policy
    resp_get_policy = await async_client.get(
        f"/api/v1/cluster/deployments/{deployment.id}/scaling-policy",
        headers=admin_auth_headers,
    )
    assert resp_get_policy.status_code == 200
    assert resp_get_policy.json()["target_metric"] == "qps"

    # 7. Evaluate Autoscaler
    resp_eval = await async_client.post(
        f"/api/v1/cluster/deployments/{deployment.id}/autoscale/evaluate?apply=false",
        headers=admin_auth_headers,
    )
    assert resp_eval.status_code == 200
    eval_data = resp_eval.json()
    assert eval_data["deployment_id"] == deployment.id
    assert eval_data["action"] in ("scale_up", "scale_down", "no_op", "cooldown")

    # 8. Update Cluster Routing Strategy
    resp_strat = await async_client.post(
        "/api/v1/cluster/strategy",
        json={"strategy": "round_robin"},
        headers=admin_auth_headers,
    )
    assert resp_strat.status_code == 200
    assert resp_strat.json()["routing_strategy"] == "round_robin"
