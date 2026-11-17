"""Unit and Integration Tests for Model Inspection and VRAM Calculation."""

import pytest
from httpx import AsyncClient

from backend.app.services.model_inspector import (
    calculate_min_vram_gb,
    infer_metadata_from_repo_name,
    inspect_huggingface_repo,
    parse_parameter_count,
)


def test_parameter_count_parser():
    """Verify parameter count strings are converted accurately."""
    val, display = parse_parameter_count("8B")
    assert val == 8.0
    assert display == "8B"

    val_70b, display_70b = parse_parameter_count("70B")
    assert val_70b == 70.0
    assert display_70b == "70B"

    val_m, display_m = parse_parameter_count("500M")
    assert val_m == 0.5


def test_vram_calculation_formula():
    """Verify realistic GPU VRAM requirements calculated across precisions."""
    # 8B BF16 (2 bytes per param): ~16GB weights + KV overhead -> ~20-22GB
    vram_8b_bf16 = calculate_min_vram_gb("8B", "BF16", context_window=8192)
    assert 18.0 <= vram_8b_bf16 <= 24.0

    # 8B INT4 (0.5 bytes per param): ~4GB weights + KV overhead -> ~6-8GB
    vram_8b_int4 = calculate_min_vram_gb("8B", "INT4", context_window=8192)
    assert 5.0 <= vram_8b_int4 <= 9.0
    assert vram_8b_int4 < vram_8b_bf16

    # 70B AWQ (0.5 bytes per param): ~32.6GB weights + 14GB KV + overhead -> ~50-55GB
    vram_70b_awq = calculate_min_vram_gb("70B", "AWQ", context_window=8192)
    assert 48.0 <= vram_70b_awq <= 56.0


@pytest.mark.asyncio
async def test_inspect_huggingface_repo_heuristic():
    """Verify offline heuristic fallback extracts proper metadata."""
    meta = await inspect_huggingface_repo("meta-llama/Llama-3.1-8B-Instruct")
    assert meta["architecture"] == "LlamaForCausalLM"
    assert meta["parameters"] == "8B"
    assert meta["precision"] == "BF16"
    assert meta["min_gpu_vram_gb"] > 16.0


@pytest.mark.asyncio
async def test_inspect_model_endpoint(async_client: AsyncClient):
    """Test POST /api/v1/models/inspect endpoint."""
    res = await async_client.post(
        "/api/v1/models/inspect",
        json={"repo_id": "mistralai/Mistral-7B-Instruct-v0.2"},
    )
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["repo_id"] == "mistralai/Mistral-7B-Instruct-v0.2"
    assert data["architecture"] in ("MistralForCausalLM", "AutoModelForCausalLM")
    assert data["parameters"] == "7B"
    assert data["min_gpu_vram_gb"] > 0


@pytest.mark.asyncio
async def test_verify_weights_endpoint(async_client: AsyncClient):
    """Test POST /api/v1/models/{id}/verify-weights endpoint."""
    # Register model first
    create_res = await async_client.post(
        "/api/v1/models",
        json={"name": "Qwen 2.5 3B", "repo_id": "Qwen/Qwen2.5-3B-Instruct"},
    )
    model_id = create_res.json()["data"]["id"]

    verify_res = await async_client.post(f"/api/v1/models/{model_id}/verify-weights")
    assert verify_res.status_code == 200
    model_data = verify_res.json()["data"]
    assert "is_downloaded" in model_data
    assert model_data["local_path"] is not None
