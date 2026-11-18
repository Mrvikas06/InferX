"""End-to-End (E2E) Full Platform Verification Test for InferX.

Validates the complete platform journey:
1. User Authentication & Identity Provisioning
2. API Key Issuance with RBAC Scopes
3. Model Registry Onboarding
4. Serving Deployment Provisioning & Port Allocation
5. Cluster Load Balancer & Replica Pool Orchestration
6. Enterprise Quota Policy Allocation
7. OpenAI-Compatible Chat Completion Inference & Token Accounting
8. Benchmarking Concurrency Sweep Execution
9. Security Audit Logging & Compliance CSV Export
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services.benchmark_runner import execute_benchmark_task


@pytest.mark.asyncio
async def test_complete_platform_e2e_lifecycle(
    async_client: AsyncClient,
    db_session: AsyncSession,
):
    """Execute complete end-to-end user and inference lifecycle."""

    # =========================================================================
    # Step 1: User Authentication & Token Acquisition
    # =========================================================================
    reg_resp = await async_client.post(
        "/api/v1/auth/register",
        json={"email": "e2e_lead@inferx.ai", "password": "Password123!"},
    )
    assert reg_resp.status_code == 201

    login_resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "e2e_lead@inferx.ai", "password": "Password123!"},
    )
    assert login_resp.status_code == 200
    token_data = login_resp.json()["data"]
    jwt_token = token_data["access_token"]
    auth_headers = {"Authorization": f"Bearer {jwt_token}"}

    # =========================================================================
    # Step 2: Issue Scoped API Key
    # =========================================================================
    key_resp = await async_client.post(
        "/api/v1/api-keys",
        json={"name": "E2E Automated Key", "role": "operator", "rate_limit_rps": 100},
        headers=auth_headers,
    )
    assert key_resp.status_code == 201
    raw_api_key = key_resp.json()["data"]["raw_key"]
    api_key_headers = {"X-API-Key": raw_api_key}

    # =========================================================================
    # Step 3: Register Model in Model Registry
    # =========================================================================
    model_payload = {
        "name": "Llama 3.3 70B E2E Model",
        "repo_id": "meta-llama/Llama-3.3-70B-E2E",
        "architecture": "AutoModelForCausalLM",
        "parameters": "70B",
        "precision": "BF16",
        "context_window": 16384,
        "is_downloaded": True,
    }
    model_resp = await async_client.post(
        "/api/v1/models",
        json=model_payload,
        headers=auth_headers,
    )
    assert model_resp.status_code == 201
    model_data = model_resp.json()["data"]
    model_id = model_data["id"]

    # =========================================================================
    # Step 4: Create Deployment
    # =========================================================================
    dep_payload = {
        "name": "e2e-llama-70b-dep",
        "model_id": model_id,
        "engine": "vLLM",
        "tensor_parallel": 4,
        "port": 8899,
        "max_model_len": 16384,
    }
    dep_resp = await async_client.post(
        "/api/v1/deployments",
        json=dep_payload,
        headers=auth_headers,
    )
    assert dep_resp.status_code == 201
    dep_data = dep_resp.json()["data"]
    dep_id = dep_data["id"]

    # Start deployment
    start_resp = await async_client.post(
        f"/api/v1/deployments/{dep_id}/start",
        headers=auth_headers,
    )
    assert start_resp.status_code == 200
    assert start_resp.json()["data"]["status"] == "running"

    # =========================================================================
    # Step 5: Scale Deployment & Check Cluster Overview
    # =========================================================================
    scale_resp = await async_client.post(
        f"/api/v1/cluster/deployments/{dep_id}/scale",
        json={"replicas": 2},
        headers=auth_headers,
    )
    assert scale_resp.status_code == 200
    assert scale_resp.json()["desired_replicas"] == 2

    overview_resp = await async_client.get(
        "/api/v1/cluster/overview",
        headers=auth_headers,
    )
    assert overview_resp.status_code == 200
    assert overview_resp.json()["total_replicas"] >= 2

    # =========================================================================
    # Step 6: Create Enterprise Token Quota Policy
    # =========================================================================
    quota_payload = {
        "name": "E2E User Quota Tier",
        "target_type": "user",
        "target_id": None,  # Global default for users
        "max_tokens_per_day": 100000,
        "max_tokens_per_month": 2000000,
        "rate_limit_rpm": 600,
        "is_active": True,
    }
    quota_resp = await async_client.post(
        "/api/v1/governance/quotas",
        json=quota_payload,
        headers=auth_headers,
    )
    assert quota_resp.status_code == 201

    # =========================================================================
    # Step 7: Execute Chat Completion Inference (OpenAI Gateway)
    # =========================================================================
    chat_payload = {
        "model": "meta-llama/Llama-3.3-70B-E2E",
        "messages": [
            {"role": "system", "content": "You are a production inference test agent."},
            {"role": "user", "content": "Execute an end-to-end smoke verification."},
        ],
        "temperature": 0.7,
        "max_tokens": 128,
        "stream": False,
    }
    chat_resp = await async_client.post(
        "/v1/chat/completions",
        json=chat_payload,
        headers=api_key_headers,
    )
    assert chat_resp.status_code == 200
    chat_data = chat_resp.json()
    assert chat_data["object"] == "chat.completion"
    assert len(chat_data["choices"]) == 1
    assert "choices" in chat_data
    assert "usage" in chat_data
    assert chat_data["usage"]["total_tokens"] > 0
    assert "X-InferX-Quota-Remaining" in chat_resp.headers

    # =========================================================================
    # Step 8: Trigger and Execute Benchmark Run
    # =========================================================================
    bench_payload = {
        "name": "E2E Validation Benchmark",
        "deployment_id": dep_id,
        "concurrency": 2,
        "num_prompts": 4,
        "input_tokens": 64,
        "output_tokens": 32,
    }
    bench_resp = await async_client.post(
        "/api/v1/benchmarks",
        json=bench_payload,
        headers=auth_headers,
    )
    assert bench_resp.status_code == 201
    bench_id = bench_resp.json()["data"]["id"]

    # Fetch report
    bench_report = await async_client.get(
        f"/api/v1/benchmarks/{bench_id}",
        headers=auth_headers,
    )
    assert bench_report.status_code == 200
    assert bench_report.json()["data"]["num_prompts"] == 4
    assert bench_report.json()["data"]["concurrency"] == 2

    # =========================================================================
    # Step 9: Audit Trail Inspection & Compliance CSV Export
    # =========================================================================
    csv_resp = await async_client.get(
        "/api/v1/audit-logs/export?format=csv",
        headers=auth_headers,
    )
    assert csv_resp.status_code == 200
    assert "text/csv" in csv_resp.headers["content-type"]
    assert "action" in csv_resp.text
