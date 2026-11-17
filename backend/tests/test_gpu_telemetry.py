"""Unit and Integration Tests for GPU Telemetry and Health Engine."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.schemas.telemetry import (
    GPUStats,
    HistoricalMetricPoint,
    InferenceMetricsSnapshot,
    SystemResourceStats,
)
from backend.app.services.gpu_monitor import get_gpu_telemetry, get_system_resources
from backend.app.services.telemetry_service import telemetry_service


def test_get_gpu_telemetry_schema():
    """Verify GPU metrics collector returns valid schema and numerical bounds."""
    gpus = get_gpu_telemetry()
    assert isinstance(gpus, list)
    assert len(gpus) >= 1

    for gpu in gpus:
        assert isinstance(gpu, GPUStats)
        assert len(gpu.name) > 0
        assert gpu.memory_total_mb > 0
        assert gpu.memory_used_mb >= 0
        assert 0.0 <= gpu.memory_utilization_pct <= 100.0
        assert 0.0 <= gpu.gpu_utilization_pct <= 100.0
        if gpu.temperature_c is not None:
            assert gpu.temperature_c > 0.0


def test_get_system_resources_schema():
    """Verify host CPU, RAM, and Disk resource statistics."""
    system = get_system_resources()
    assert isinstance(system, SystemResourceStats)
    assert system.cpu_count >= 1
    assert 0.0 <= system.cpu_utilization_pct <= 100.0
    assert system.ram_total_gb > 0.0
    assert system.disk_total_gb > 0.0


def test_telemetry_service_percentiles():
    """Verify rolling percentile calculations for inference latency."""
    # Record known latencies: 10, 20, 30, ..., 100
    for latency in range(10, 110, 10):
        telemetry_service.record_inference_event(
            latency_ms=float(latency),
            ttft_ms=float(latency * 0.4),
            prompt_tokens=32,
            completion_tokens=64,
        )

    snapshot = telemetry_service.get_live_inference_snapshot(active_deployments_count=2)
    assert isinstance(snapshot, InferenceMetricsSnapshot)
    assert snapshot.latency_p50_ms <= snapshot.latency_p95_ms <= snapshot.latency_p99_ms
    assert snapshot.avg_ttft_ms > 0
    assert snapshot.active_deployments == 2


@pytest.mark.asyncio
async def test_telemetry_overview_endpoint(async_client: AsyncClient):
    """Test GET /api/v1/telemetry/overview returns aggregated observability snapshot."""
    resp = await async_client.get("/api/v1/telemetry/overview")
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    data = body["data"]

    # GPUs
    assert "gpus" in data
    assert len(data["gpus"]) >= 1
    assert "memory_total_mb" in data["gpus"][0]

    # Host System
    assert "system" in data
    assert data["system"]["cpu_count"] >= 1
    assert data["system"]["ram_total_gb"] > 0

    # Inference Snapshot
    assert "inference" in data
    assert "qps" in data["inference"]
    assert "latency_p95_ms" in data["inference"]


@pytest.mark.asyncio
async def test_telemetry_gpus_and_history_endpoints(async_client: AsyncClient):
    """Test GET /api/v1/telemetry/gpus and /history endpoints."""
    # GPUs endpoint
    gpu_resp = await async_client.get("/api/v1/telemetry/gpus")
    assert gpu_resp.status_code == 200
    gpu_data = gpu_resp.json()["data"]
    assert isinstance(gpu_data, list)
    assert len(gpu_data) >= 1

    # History endpoint
    hist_resp = await async_client.get("/api/v1/telemetry/history")
    assert hist_resp.status_code == 200
    hist_data = hist_resp.json()["data"]
    assert isinstance(hist_data, list)
    assert len(hist_data) >= 1
    first_pt = hist_data[0]
    assert "timestamp" in first_pt
    assert "qps" in first_pt
    assert "vram_used_mb" in first_pt
