"""Tests for Prometheus Metrics Scrape Endpoint and Observability Telemetry."""

import pytest
from httpx import ASGITransport, AsyncClient

from backend.app.main import app


@pytest.mark.asyncio
async def test_prometheus_metrics_scrape():
    """Verify that /metrics returns valid OpenMetrics formatted Prometheus lines."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/metrics")
        assert response.status_code == 200
        content = response.text

        # Verify critical metric keys exist in exposition format
        assert "inferx_active_requests" in content
        assert "inferx_requests_total" in content
        assert "inferx_qps" in content
        assert "inferx_tokens_per_second" in content
        assert "inferx_latency_p95_ms" in content
        assert "inferx_kv_cache_usage_percent" in content
        assert "inferx_gpu_utilization_percent" in content
