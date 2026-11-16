"""API Integration Tests for Model Registry and Deployment Management."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_and_get_model(async_client: AsyncClient):
    """Test creating and retrieving a registered model via REST API."""
    payload = {
        "name": "Meta Llama 3.1 8B Instruct",
        "repo_id": "meta-llama/Meta-Llama-3.1-8B-Instruct",
        "architecture": "LlamaForCausalLM",
        "parameters": "8B",
        "context_window": 131072,
        "precision": "BF16",
        "size_on_disk_gb": 16.0,
        "min_gpu_vram_gb": 18.0,
        "tags": ["chat", "general"],
    }

    create_res = await async_client.post("/api/v1/models", json=payload)
    assert create_res.status_code == 201
    created_data = create_res.json()["data"]
    assert created_data["id"] is not None
    assert created_data["repo_id"] == payload["repo_id"]
    model_id = created_data["id"]

    # Retrieve by ID
    get_res = await async_client.get(f"/api/v1/models/{model_id}")
    assert get_res.status_code == 200
    assert get_res.json()["data"]["name"] == payload["name"]


@pytest.mark.asyncio
async def test_duplicate_repo_id_conflict(async_client: AsyncClient):
    """Verify 409 Conflict when attempting to register duplicate model repo_id."""
    payload = {
        "name": "Qwen 2.5 Coder 7B",
        "repo_id": "Qwen/Qwen2.5-Coder-7B-Instruct",
        "architecture": "Qwen2ForCausalLM",
    }

    res1 = await async_client.post("/api/v1/models", json=payload)
    assert res1.status_code == 201

    res2 = await async_client.post("/api/v1/models", json=payload)
    assert res2.status_code == 409
    assert "already registered" in res2.json()["detail"]


@pytest.mark.asyncio
async def test_list_and_filter_models(async_client: AsyncClient):
    """Verify pagination and query filtering across registered models."""
    models_to_create = [
        {"name": "DeepSeek R1 Distill 8B", "repo_id": "deepseek-ai/DeepSeek-R1-Distill-Llama-8B", "precision": "BF16"},
        {"name": "DeepSeek R1 Distill 14B", "repo_id": "deepseek-ai/DeepSeek-R1-Distill-Qwen-14B", "precision": "AWQ"},
        {"name": "Gemma 2 9B", "repo_id": "google/gemma-2-9b-it", "precision": "BF16"},
    ]

    for m in models_to_create:
        res = await async_client.post("/api/v1/models", json=m)
        assert res.status_code == 201

    # Search keyword
    search_res = await async_client.get("/api/v1/models?query=deepseek")
    assert search_res.status_code == 200
    search_data = search_res.json()["data"]
    assert search_data["total"] == 2
    assert len(search_data["items"]) == 2

    # Filter precision
    prec_res = await async_client.get("/api/v1/models?precision=AWQ")
    assert prec_res.status_code == 200
    prec_data = prec_res.json()["data"]
    assert prec_data["total"] == 1
    assert prec_data["items"][0]["repo_id"] == "deepseek-ai/DeepSeek-R1-Distill-Qwen-14B"


@pytest.mark.asyncio
async def test_patch_model(async_client: AsyncClient):
    """Verify updating model metadata and tags."""
    create_res = await async_client.post(
        "/api/v1/models",
        json={"name": "Phi 3 Mini", "repo_id": "microsoft/Phi-3-mini-4k-instruct"},
    )
    model_id = create_res.json()["data"]["id"]

    patch_res = await async_client.patch(
        f"/api/v1/models/{model_id}",
        json={"context_window": 128000, "is_downloaded": True},
    )
    assert patch_res.status_code == 200
    updated_data = patch_res.json()["data"]
    assert updated_data["context_window"] == 128000
    assert updated_data["is_downloaded"] is True


@pytest.mark.asyncio
async def test_deployment_lifecycle_and_constraints(async_client: AsyncClient):
    """Test deployment registration, port uniqueness, model integrity check, and deletion."""
    # 1. Create model first
    model_res = await async_client.post(
        "/api/v1/models",
        json={"name": "Llama 3 8B", "repo_id": "meta-llama/Llama-3-8B-Instruct"},
    )
    model_id = model_res.json()["data"]["id"]

    # 2. Attempt deployment with fake model ID -> 404
    fake_dep_res = await async_client.post(
        "/api/v1/deployments",
        json={
            "name": "fake-deployment",
            "model_id": "00000000-0000-0000-0000-000000000000",
            "port": 8001,
        },
    )
    assert fake_dep_res.status_code == 404

    # 3. Create valid deployment
    dep_payload = {
        "name": "llama-production-v1",
        "model_id": model_id,
        "engine": "vLLM",
        "tensor_parallel": 1,
        "port": 8000,
        "max_model_len": 8192,
    }
    dep_res = await async_client.post("/api/v1/deployments", json=dep_payload)
    assert dep_res.status_code == 201
    dep_data = dep_res.json()["data"]
    dep_id = dep_data["id"]
    assert dep_data["port"] == 8000
    assert dep_data["base_url"] == "http://localhost:8000/v1"
    assert dep_data["model"]["name"] == "Llama 3 8B"

    # 4. Attempt duplicate port -> 409
    dup_port_res = await async_client.post(
        "/api/v1/deployments",
        json={
            "name": "llama-staging",
            "model_id": model_id,
            "port": 8000,
        },
    )
    assert dup_port_res.status_code == 409
    assert "already assigned" in dup_port_res.json()["detail"]

    # 5. Prevent deleting model with active deployment -> 400
    del_model_res = await async_client.delete(f"/api/v1/models/{model_id}")
    assert del_model_res.status_code == 400
    assert "currently referenced" in del_model_res.json()["detail"]

    # 6. Update deployment status
    patch_dep_res = await async_client.patch(
        f"/api/v1/deployments/{dep_id}",
        json={"status": "running", "kv_cache_usage": 42.5, "qps": 18.2},
    )
    assert patch_dep_res.status_code == 200
    assert patch_dep_res.json()["data"]["status"] == "running"
    assert patch_dep_res.json()["data"]["kv_cache_usage"] == 42.5

    # 7. Delete deployment, then delete model
    del_dep_res = await async_client.delete(f"/api/v1/deployments/{dep_id}")
    assert del_dep_res.status_code == 200

    del_model_clean = await async_client.delete(f"/api/v1/models/{model_id}")
    assert del_model_clean.status_code == 200
