"""Deployment Management API Endpoints for InferX."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.v1.schemas import APIResponse
from backend.app.core.logging import get_correlation_id
from backend.app.db.session import get_db
from backend.app.repositories.deployment_repository import deployment_repository
from backend.app.repositories.model_repository import model_repository
from backend.app.schemas.deployment import (
    DeploymentCreate,
    DeploymentListResponse,
    DeploymentResponse,
    DeploymentUpdate,
)

router = APIRouter()


@router.get("", response_model=APIResponse[DeploymentListResponse])
async def list_deployments(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by operational status"),
    engine: Optional[str] = Query(None, description="Filter by engine (vLLM, SGLang, TensorRT-LLM)"),
    skip: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(20, ge=1, le=100, description="Page limit"),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[DeploymentListResponse]:
    """List and filter active or configured deployments."""
    items = await deployment_repository.list_deployments(
        db,
        status=status_filter,
        engine=engine,
        skip=skip,
        limit=limit,
    )
    total = await deployment_repository.count_filtered(
        db,
        status=status_filter,
        engine=engine,
    )
    return APIResponse[DeploymentListResponse](
        success=True,
        data=DeploymentListResponse(
            items=[DeploymentResponse.model_validate(d) for d in items],
            total=total,
            skip=skip,
            limit=limit,
        ),
        correlation_id=get_correlation_id(),
    )


@router.post("", response_model=APIResponse[DeploymentResponse], status_code=status.HTTP_201_CREATED)
async def create_deployment(
    payload: DeploymentCreate,
    db: AsyncSession = Depends(get_db),
) -> APIResponse[DeploymentResponse]:
    """Register and allocate an inference serving deployment endpoint."""
    # 1. Validate that referenced model exists
    target_model = await model_repository.get(db, payload.model_id)
    if not target_model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Target Model with ID '{payload.model_id}' does not exist in registry",
        )

    # 2. Validate deployment name uniqueness
    existing_name = await deployment_repository.get_by_name(db, payload.name)
    if existing_name:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Deployment with name '{payload.name}' already exists (id: {existing_name.id})",
        )

    # 3. Validate port availability
    existing_port = await deployment_repository.get_by_port(db, payload.port)
    if existing_port:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Port {payload.port} is already assigned to deployment '{existing_port.name}'",
        )

    # Automatically construct default base_url if not provided
    create_dict = payload.model_dump()
    if not create_dict.get("base_url"):
        create_dict["base_url"] = f"http://localhost:{payload.port}/v1"

    deployment = await deployment_repository.create(db, create_dict)
    # Eager load the model relationship
    loaded = await deployment_repository.get_with_model(db, deployment.id)
    return APIResponse[DeploymentResponse](
        success=True,
        data=DeploymentResponse.model_validate(loaded or deployment),
        correlation_id=get_correlation_id(),
    )


@router.get("/{deployment_id}", response_model=APIResponse[DeploymentResponse])
async def get_deployment(
    deployment_id: str,
    db: AsyncSession = Depends(get_db),
) -> APIResponse[DeploymentResponse]:
    """Retrieve detailed deployment configuration and real-time telemetry."""
    deployment = await deployment_repository.get_with_model(db, deployment_id)
    if not deployment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deployment with ID '{deployment_id}' not found",
        )
    return APIResponse[DeploymentResponse](
        success=True,
        data=DeploymentResponse.model_validate(deployment),
        correlation_id=get_correlation_id(),
    )


@router.patch("/{deployment_id}", response_model=APIResponse[DeploymentResponse])
async def update_deployment(
    deployment_id: str,
    payload: DeploymentUpdate,
    db: AsyncSession = Depends(get_db),
) -> APIResponse[DeploymentResponse]:
    """Update runtime status, replica count, or telemetry for a deployment."""
    deployment = await deployment_repository.get_with_model(db, deployment_id)
    if not deployment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deployment with ID '{deployment_id}' not found",
        )

    if payload.port is not None and payload.port != deployment.port:
        existing_port = await deployment_repository.get_by_port(db, payload.port)
        if existing_port and existing_port.id != deployment.id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Port {payload.port} is already in use by deployment '{existing_port.name}'",
            )

    updated = await deployment_repository.update(db, deployment, payload)
    loaded = await deployment_repository.get_with_model(db, updated.id)
    return APIResponse[DeploymentResponse](
        success=True,
        data=DeploymentResponse.model_validate(loaded or updated),
        correlation_id=get_correlation_id(),
    )


@router.delete("/{deployment_id}", response_model=APIResponse[DeploymentResponse])
async def delete_deployment(
    deployment_id: str,
    db: AsyncSession = Depends(get_db),
) -> APIResponse[DeploymentResponse]:
    """Terminate and remove a serving deployment endpoint."""
    deployment = await deployment_repository.get_with_model(db, deployment_id)
    if not deployment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deployment with ID '{deployment_id}' not found",
        )

    deleted = await deployment_repository.delete(db, deployment_id)
    return APIResponse[DeploymentResponse](
        success=True,
        data=DeploymentResponse.model_validate(deleted),
        correlation_id=get_correlation_id(),
    )
