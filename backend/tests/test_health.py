"""Unit and Integration Tests for InferX Health, System, and Middleware."""

import pytest
from httpx import AsyncClient

from backend.app.core.config import get_settings


@pytest.mark.asyncio
async def test_health_endpoint(async_client: AsyncClient):
    """Verify /health returns 200 and expected payload structure."""
    response = await async_client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert data["app_name"] == "InferX"
    assert "components" in data
    assert "api" in data["components"]
    assert data["components"]["api"]["status"] == "healthy"


@pytest.mark.asyncio
async def test_liveness_endpoint(async_client: AsyncClient):
    """Verify /health/live container probe."""
    response = await async_client.get("/health/live")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "live"
    assert data["app"] == "InferX"


@pytest.mark.asyncio
async def test_readiness_endpoint(async_client: AsyncClient):
    """Verify /health/ready readiness probe."""
    response = await async_client.get("/health/ready")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "ready"
    assert "runtime" in data["components"]


@pytest.mark.asyncio
async def test_platform_info_endpoint(async_client: AsyncClient):
    """Verify /api/v1/info returns system metadata and hardware context."""
    response = await async_client.get("/api/v1/info")
    assert response.status_code == 200

    payload = response.json()
    assert payload["success"] is True
    assert payload["data"] is not None

    data = payload["data"]
    assert data["name"] == "InferX"
    assert "vLLM" in data["supported_engines"]
    assert "SGLang" in data["supported_engines"]
    assert "TensorRT-LLM" in data["supported_engines"]

    hw = data["hardware"]
    assert hw["cpu_count"] >= 1
    assert hw["memory_total_gb"] > 0
    assert hw["memory_available_gb"] > 0
    assert isinstance(hw["gpu_available"], bool)


@pytest.mark.asyncio
async def test_correlation_id_generated(async_client: AsyncClient):
    """Verify correlation ID is automatically assigned and returned in headers."""
    response = await async_client.get("/health")
    assert response.status_code == 200

    request_id = response.headers.get("X-Request-ID")
    assert request_id is not None
    assert len(request_id) > 8

    response_time = response.headers.get("X-Response-Time")
    assert response_time is not None
    assert response_time.endswith("ms")


@pytest.mark.asyncio
async def test_correlation_id_propagated(async_client: AsyncClient):
    """Verify client-supplied correlation ID is preserved and echoed."""
    custom_cid = "client-trace-id-xyz-12345"
    response = await async_client.get("/health", headers={"X-Request-ID": custom_cid})
    assert response.status_code == 200
    assert response.headers.get("X-Request-ID") == custom_cid


def test_config_loader():
    """Verify configuration loads with correct defaults."""
    settings = get_settings()
    assert settings.APP_NAME == "InferX"
    assert settings.BACKEND_PORT == 8000
    assert "http://localhost:3000" in settings.CORS_ORIGINS
