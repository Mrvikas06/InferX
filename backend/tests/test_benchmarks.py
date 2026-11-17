"""Unit and Integration Tests for Inference Benchmarking Suite."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.deployment import Deployment
from backend.app.models.model import Model
from backend.app.repositories.benchmark_repository import benchmark_repository
from backend.app.repositories.deployment_repository import deployment_repository
from backend.app.repositories.model_repository import model_repository
from backend.app.schemas.deployment import DeploymentCreate
from backend.app.schemas.model import ModelCreate
from backend.app.services.benchmark_runner import execute_benchmark_task


@pytest.mark.asyncio
async def test_benchmark_full_lifecycle(db_session: AsyncSession, async_client: AsyncClient):
    """Test creating, executing, and retrieving benchmark results."""
    # 1. Setup Model and Deployment
    model = await model_repository.create(
        db_session,
        ModelCreate(
            name="Benchmark Llama 8B",
            repo_id="meta-llama/Llama-3.1-8B-Benchmark",
            parameters="8B",
        ),
    )
    deployment = await deployment_repository.create(
        db_session,
        DeploymentCreate(
            model_id=model.id,
            name="bench-dep-8095",
            port=8095,
            engine="vLLM",
        ),
    )
    await db_session.commit()

    # 2. Trigger Benchmark Creation via API
    payload = {
        "name": "Llama 8B Concurrency 4 Sweep",
        "deployment_id": deployment.id,
        "concurrency": 4,
        "num_prompts": 8,
        "input_tokens": 128,
        "output_tokens": 64,
    }
    create_resp = await async_client.post("/api/v1/benchmarks", json=payload)
    assert create_resp.status_code == 201
    created_data = create_resp.json()["data"]
    benchmark_id = created_data["id"]
    assert created_data["name"] == payload["name"]
    assert created_data["concurrency"] == 4
    assert created_data["status"] in ["queued", "running"]

    # 3. Execute the benchmark task directly
    await execute_benchmark_task(benchmark_id, session=db_session)

    # 4. Fetch detailed report
    get_resp = await async_client.get(f"/api/v1/benchmarks/{benchmark_id}")
    assert get_resp.status_code == 200
    report = get_resp.json()["data"]
    assert report["status"] == "completed"
    assert report["rps"] > 0
    assert report["tokens_per_sec"] > 0
    assert report["p50_latency_ms"] > 0
    assert report["p95_latency_ms"] >= report["p50_latency_ms"]
    assert report["mean_tpot_ms"] > 0
    assert "results_json" in report
    assert "latency_histogram" in report["results_json"]

    # 5. List benchmarks
    list_resp = await async_client.get(f"/api/v1/benchmarks?deployment_id={deployment.id}")
    assert list_resp.status_code == 200
    list_data = list_resp.json()["data"]
    assert list_data["total"] >= 1
    assert any(b["id"] == benchmark_id for b in list_data["items"])

    # 6. Delete benchmark
    del_resp = await async_client.delete(f"/api/v1/benchmarks/{benchmark_id}")
    assert del_resp.status_code == 200

    # Verify 404 after deletion
    verify_resp = await async_client.get(f"/api/v1/benchmarks/{benchmark_id}")
    assert verify_resp.status_code == 404
