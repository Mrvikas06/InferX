"""Unit and Integration Tests for OpenAI-Compatible Inference Gateway."""

import json
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.rate_limit import reset_rate_limits
from backend.app.core.security import generate_api_key
from backend.app.models.deployment import Deployment
from backend.app.models.model import Model
from backend.app.models.user import User
from backend.app.repositories.api_key_repository import api_key_repository
from backend.app.repositories.deployment_repository import deployment_repository
from backend.app.repositories.model_repository import model_repository
from backend.app.repositories.user_repository import user_repository
from backend.app.schemas.api_key import ApiKeyCreate
from backend.app.schemas.auth import UserRegister
from backend.app.schemas.deployment import DeploymentCreate
from backend.app.schemas.model import ModelCreate
from backend.app.services.deployment_manager import (
    start_deployment_lifecycle,
    stop_deployment_lifecycle,
)
from backend.app.services.vllm_runner import stop_engine


@pytest.fixture(autouse=True)
async def cleanup_engines():
    """Ensure rate limits and engine states are reset between tests."""
    reset_rate_limits()
    yield
    reset_rate_limits()


@pytest.mark.asyncio
async def test_openai_models_endpoint_lifecycle(db_session: AsyncSession, async_client: AsyncClient):
    """Test GET /v1/models reflects active serving models."""
    # Initially empty
    resp = await async_client.get("/v1/models")
    assert resp.status_code == 200
    data = resp.json()
    assert data["object"] == "list"
    assert isinstance(data["data"], list)

    # Register model and start deployment
    model = await model_repository.create(
        db_session,
        ModelCreate(
            name="Qwen 2.5 7B",
            repo_id="Qwen/Qwen2.5-7B-Instruct",
            parameters="7B",
            architecture="Qwen2ForCausalLM",
        ),
    )
    deployment = await deployment_repository.create(
        db_session,
        DeploymentCreate(
            model_id=model.id,
            name="qwen-gateway-test",
            port=8089,
            engine="vllm",
        ),
    )
    await db_session.commit()

    # Stopped deployment should not appear in /v1/models
    resp_after_create = await async_client.get("/v1/models")
    model_ids = [m["id"] for m in resp_after_create.json()["data"]]
    assert "Qwen/Qwen2.5-7B-Instruct" not in model_ids

    # Start deployment
    deployment = await deployment_repository.get_with_model(db_session, deployment.id)
    assert deployment is not None
    await start_deployment_lifecycle(db_session, deployment)
    await db_session.commit()

    # Now active model should be listed
    resp_after_start = await async_client.get("/v1/models")
    assert resp_after_start.status_code == 200
    active_ids = [m["id"] for m in resp_after_start.json()["data"]]
    assert "Qwen/Qwen2.5-7B-Instruct" in active_ids

    # Cleanup
    await stop_deployment_lifecycle(db_session, deployment)
    await db_session.commit()


@pytest.mark.asyncio
async def test_chat_completions_auth_and_errors(db_session: AsyncSession, async_client: AsyncClient):
    """Test auth enforcement and OpenAI error contracts."""
    # 1. Unauthorized request
    unauth_resp = await async_client.post(
        "/v1/chat/completions",
        json={
            "model": "meta-llama/Llama-3.1-8B-Instruct",
            "messages": [{"role": "user", "content": "Hello"}],
        },
    )
    assert unauth_resp.status_code == 401

    # Create user and API Key
    user = await user_repository.create_user(
        db_session,
        UserRegister(
            email="gateway_tester@inferx.local",
            password="Password123!",
            full_name="Gateway Tester",
            role="operator",
        ),
    )
    api_key_obj, raw_key = await api_key_repository.create_api_key(
        db_session,
        ApiKeyCreate(name="Gateway Key", role="operator"),
        user_id=user.id,
    )
    await db_session.commit()

    auth_headers = {"Authorization": f"Bearer {raw_key}"}

    # 2. Model not found error
    not_found_resp = await async_client.post(
        "/v1/chat/completions",
        headers=auth_headers,
        json={
            "model": "non-existent/fake-model-xyz",
            "messages": [{"role": "user", "content": "Hello"}],
        },
    )
    assert not_found_resp.status_code == 404
    error_payload = not_found_resp.json()
    assert "error" in error_payload
    assert error_payload["error"]["code"] == "model_not_found"

    # 3. Model exists but stopped
    model = await model_repository.create(
        db_session,
        ModelCreate(
            name="Llama 3 Stopped",
            repo_id="meta-llama/Llama-3-Stopped-Test",
            parameters="8B",
        ),
    )
    await deployment_repository.create(
        db_session,
        DeploymentCreate(
            model_id=model.id,
            name="llama3-stopped-dep",
            port=8091,
        ),
    )
    await db_session.commit()

    stopped_resp = await async_client.post(
        "/v1/chat/completions",
        headers=auth_headers,
        json={
            "model": "meta-llama/Llama-3-Stopped-Test",
            "messages": [{"role": "user", "content": "Are you running?"}],
        },
    )
    assert stopped_resp.status_code == 400
    assert stopped_resp.json()["error"]["code"] == "model_stopped"


@pytest.mark.asyncio
async def test_chat_completions_non_streaming_execution(db_session: AsyncSession, async_client: AsyncClient):
    """Test full non-streaming inference pass-through."""
    # Create user & auth
    user = await user_repository.create_user(
        db_session,
        UserRegister(
            email="inference_user@inferx.local",
            password="Password123!",
            full_name="Inference User",
            role="operator",
        ),
    )
    api_key_obj, raw_key = await api_key_repository.create_api_key(
        db_session,
        ApiKeyCreate(name="Inference Test Key", role="operator"),
        user_id=user.id,
    )

    # Create model & running deployment
    model = await model_repository.create(
        db_session,
        ModelCreate(
            name="Llama 3.1 8B",
            repo_id="meta-llama/Llama-3.1-8B-Instruct",
            parameters="8B",
        ),
    )
    dep = await deployment_repository.create(
        db_session,
        DeploymentCreate(
            model_id=model.id,
            name="llama31-running-dep",
            port=8092,
        ),
    )
    await db_session.commit()

    # Start deployment
    dep = await deployment_repository.get_with_model(db_session, dep.id)
    assert dep is not None
    await start_deployment_lifecycle(db_session, dep)
    await db_session.commit()

    # Send chat completion
    resp = await async_client.post(
        "/v1/chat/completions",
        headers={"Authorization": f"Bearer {raw_key}"},
        json={
            "model": "meta-llama/Llama-3.1-8B-Instruct",
            "messages": [
                {"role": "system", "content": "You are a helpful coding assistant."},
                {"role": "user", "content": "Write a python quicksort function."},
            ],
            "temperature": 0.2,
            "stream": False,
        },
    )

    assert resp.status_code == 200
    assert "X-InferX-Latency-Ms" in resp.headers
    data = resp.json()
    assert data["object"] == "chat.completion"
    assert data["model"] == "meta-llama/Llama-3.1-8B-Instruct"
    assert len(data["choices"]) > 0
    assert data["choices"][0]["message"]["role"] == "assistant"
    assert len(data["choices"][0]["message"]["content"]) > 0
    assert data["usage"]["total_tokens"] > 0

    # Cleanup
    await stop_deployment_lifecycle(db_session, dep)
    await db_session.commit()


@pytest.mark.asyncio
async def test_chat_completions_streaming_sse(db_session: AsyncSession, async_client: AsyncClient):
    """Test Server-Sent Events (SSE) streaming token chunks."""
    # Create user & auth
    user = await user_repository.create_user(
        db_session,
        UserRegister(
            email="stream_user@inferx.local",
            password="Password123!",
            full_name="Stream User",
            role="operator",
        ),
    )
    api_key_obj, raw_key = await api_key_repository.create_api_key(
        db_session,
        ApiKeyCreate(name="Stream Key", role="operator"),
        user_id=user.id,
    )

    model = await model_repository.create(
        db_session,
        ModelCreate(
            name="Mistral 7B",
            repo_id="mistralai/Mistral-7B-Instruct-v0.3",
            parameters="7B",
        ),
    )
    dep = await deployment_repository.create(
        db_session,
        DeploymentCreate(
            model_id=model.id,
            name="mistral-stream-dep",
            port=8093,
        ),
    )
    await db_session.commit()

    dep = await deployment_repository.get_with_model(db_session, dep.id)
    assert dep is not None
    await start_deployment_lifecycle(db_session, dep)
    await db_session.commit()

    resp = await async_client.post(
        "/api/v1/chat/completions",
        headers={"Authorization": f"Bearer {raw_key}"},
        json={
            "model": "mistralai/Mistral-7B-Instruct-v0.3",
            "messages": [{"role": "user", "content": "Stream me a response"}],
            "stream": True,
        },
    )

    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers["content-type"]

    body_text = resp.text
    assert "data:" in body_text
    assert "[DONE]" in body_text

    # Verify chunks contain chat.completion.chunk objects
    lines = [line.strip() for line in body_text.splitlines() if line.startswith("data:")]
    valid_chunks = 0
    for line in lines:
        payload_str = line.replace("data:", "").strip()
        if payload_str == "[DONE]":
            continue
        chunk_dict = json.loads(payload_str)
        assert chunk_dict["object"] == "chat.completion.chunk"
        valid_chunks += 1

    assert valid_chunks >= 2

    # Cleanup
    await stop_deployment_lifecycle(db_session, dep)
    await db_session.commit()
