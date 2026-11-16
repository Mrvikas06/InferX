"""Tests for Database Models, Relationships, and Base Repositories."""

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.api_key import ApiKey
from backend.app.models.audit_log import AuditLog
from backend.app.models.deployment import Deployment
from backend.app.models.model import Model
from backend.app.repositories.deployment_repository import deployment_repository
from backend.app.repositories.model_repository import model_repository
from backend.app.schemas.deployment import DeploymentCreate
from backend.app.schemas.model import ModelCreate, ModelUpdate


@pytest.mark.asyncio
async def test_create_model_entity(db_session: AsyncSession):
    """Verify Model persistence, UUID generation, and timestamp mixin."""
    model_in = ModelCreate(
        name="Meta Llama 3.1 8B",
        repo_id="meta-llama/Llama-3.1-8B-Instruct",
        architecture="LlamaForCausalLM",
        parameters="8B",
        context_window=131072,
        precision="BF16",
        size_on_disk_gb=16.0,
        min_gpu_vram_gb=18.0,
        tags=["general", "reasoning"],
    )

    created = await model_repository.create(db_session, model_in)
    assert created.id is not None
    assert len(created.id) == 36
    assert created.created_at is not None
    assert created.updated_at is not None
    assert created.name == "Meta Llama 3.1 8B"
    assert created.tags == ["general", "reasoning"]

    # Verify query by repo_id
    fetched = await model_repository.get_by_repo_id(db_session, "meta-llama/Llama-3.1-8B-Instruct")
    assert fetched is not None
    assert fetched.id == created.id


@pytest.mark.asyncio
async def test_model_unique_repo_id(db_session: AsyncSession):
    """Verify unique constraint on Model repo_id."""
    model_in = ModelCreate(
        name="Mistral 7B",
        repo_id="mistralai/Mistral-7B-v0.1",
    )
    await model_repository.create(db_session, model_in)

    # Attempting to insert duplicate repo_id should fail
    duplicate = ModelCreate(
        name="Mistral Duplicate",
        repo_id="mistralai/Mistral-7B-v0.1",
    )
    with pytest.raises(IntegrityError):
        await model_repository.create(db_session, duplicate)
    await db_session.rollback()


@pytest.mark.asyncio
async def test_deployment_model_relationship(db_session: AsyncSession):
    """Verify Deployment foreign key and joined relationship with Model."""
    model = await model_repository.create(
        db_session,
        ModelCreate(
            name="Qwen 2.5 7B",
            repo_id="Qwen/Qwen2.5-7B-Instruct",
            architecture="Qwen2ForCausalLM",
        ),
    )

    dep_in = DeploymentCreate(
        name="qwen-prod-primary",
        model_id=model.id,
        engine="vLLM",
        tensor_parallel=1,
        port=8001,
        max_model_len=32768,
        gpu_type="NVIDIA RTX 4090",
    )

    dep = await deployment_repository.create(db_session, dep_in)
    assert dep.id is not None
    assert dep.model_id == model.id
    assert dep.status == "stopped"

    # Query with eager model loading
    loaded = await deployment_repository.get_with_model(db_session, dep.id)
    assert loaded is not None
    assert loaded.model.repo_id == "Qwen/Qwen2.5-7B-Instruct"


@pytest.mark.asyncio
async def test_deployment_port_uniqueness(db_session: AsyncSession):
    """Verify unique port enforcement across deployments."""
    model = await model_repository.create(
        db_session,
        ModelCreate(name="Model A", repo_id="org/model-a"),
    )

    dep1 = DeploymentCreate(
        name="dep-1",
        model_id=model.id,
        port=8080,
    )
    await deployment_repository.create(db_session, dep1)

    dep2 = DeploymentCreate(
        name="dep-2",
        model_id=model.id,
        port=8080,
    )
    with pytest.raises(IntegrityError):
        await deployment_repository.create(db_session, dep2)
    await db_session.rollback()


@pytest.mark.asyncio
async def test_api_key_and_audit_log_entities(db_session: AsyncSession):
    """Verify ApiKey and AuditLog model definitions."""
    key = ApiKey(
        name="CI Service Key",
        prefix="ifx_live",
        key_hash="sha256_mock_hash",
        rate_limit_rps=120,
    )
    db_session.add(key)
    await db_session.flush()
    assert key.id is not None
    assert key.is_active is True

    audit = AuditLog(
        action="deployment.create",
        resource_type="deployment",
        resource_id="dep-1234",
        details={"engine": "vLLM", "port": 8000},
    )
    db_session.add(audit)
    await db_session.flush()
    assert audit.id is not None
    assert audit.created_at is not None
