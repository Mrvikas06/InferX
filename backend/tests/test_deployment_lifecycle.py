"""Integration Tests for Deployment Lifecycle, Automatic Port Allocation, and Health Probes."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_automatic_port_allocation(async_client: AsyncClient):
    """Verify that omitting port automatically assigns an available port from pool."""
    model_res = await async_client.post(
        "/api/v1/models",
        json={"name": "Auto Port Model", "repo_id": "org/auto-port-model"},
    )
    model_id = model_res.json()["data"]["id"]

    dep_res = await async_client.post(
        "/api/v1/deployments",
        json={
            "name": "auto-port-deployment",
            "model_id": model_id,
            "engine": "vLLM",
            # port is omitted!
        },
    )
    assert dep_res.status_code == 201
    dep_data = dep_res.json()["data"]
    assert dep_data["port"] is not None
    assert 8001 <= dep_data["port"] <= 8999
    assert f":{dep_data['port']}/v1" in dep_data["base_url"]


@pytest.mark.asyncio
async def test_start_stop_restart_lifecycle(async_client: AsyncClient):
    """Test state machine transitions across start, stop, restart, and invalid triggers."""
    model_res = await async_client.post(
        "/api/v1/models",
        json={"name": "Lifecycle Model", "repo_id": "org/lifecycle-model"},
    )
    model_id = model_res.json()["data"]["id"]

    create_res = await async_client.post(
        "/api/v1/deployments",
        json={"name": "lifecycle-dep", "model_id": model_id, "port": 8100},
    )
    dep_id = create_res.json()["data"]["id"]
    assert create_res.json()["data"]["status"] == "stopped"

    # Stopping an already stopped deployment -> 400 Bad Request
    invalid_stop = await async_client.post(f"/api/v1/deployments/{dep_id}/stop")
    assert invalid_stop.status_code == 400
    assert "already stopped" in invalid_stop.json()["detail"]

    # Start deployment -> running
    start_res = await async_client.post(f"/api/v1/deployments/{dep_id}/start")
    assert start_res.status_code == 200
    assert start_res.json()["data"]["status"] == "running"
    assert start_res.json()["data"]["kv_cache_usage"] > 0

    # Starting an already running deployment -> 400 Bad Request
    invalid_start = await async_client.post(f"/api/v1/deployments/{dep_id}/start")
    assert invalid_start.status_code == 400
    assert "already running" in invalid_start.json()["detail"]

    # Probe health while running
    health_res = await async_client.get(f"/api/v1/deployments/{dep_id}/health")
    assert health_res.status_code == 200
    health_data = health_res.json()["data"]
    assert health_data["healthy"] is True

    # Retrieve logs
    logs_res = await async_client.get(f"/api/v1/deployments/{dep_id}/logs")
    assert logs_res.status_code == 200
    logs_data = logs_res.json()["data"]
    assert logs_data["total_lines"] >= 2
    assert any("Initializing inference engine" in entry["message"] for entry in logs_data["logs"])

    # Restart deployment -> running
    restart_res = await async_client.post(f"/api/v1/deployments/{dep_id}/restart")
    assert restart_res.status_code == 200
    assert restart_res.json()["data"]["status"] == "running"

    # Stop deployment -> stopped
    stop_res = await async_client.post(f"/api/v1/deployments/{dep_id}/stop")
    assert stop_res.status_code == 200
    assert stop_res.json()["data"]["status"] == "stopped"
