"""Deployment Management and Lifecycle Control API Endpoints for InferX."""

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
    DeploymentHealthProbeResponse,
    DeploymentListResponse,
    DeploymentLogEntry,
    DeploymentLogsResponse,
    DeploymentResponse,
    DeploymentUpdate,
)
from backend.app.services.deployment_manager import (
    allocate_available_port,
    get_deployment_logs,
    probe_deployment_health,
    restart_deployment_lifecycle,
    start_deployment_lifecycle,
    stop_deployment_lifecycle,
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

    create_dict = payload.model_dump()

    # 3. Port allocation and validation
    if create_dict.get("port") is None or create_dict.get("port") == 0:
        assigned_port = await allocate_available_port(db)
        create_dict["port"] = assigned_port
    else:
        existing_port = await deployment_repository.get_by_port(db, create_dict["port"])
        if existing_port:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Port {create_dict['port']} is already assigned to deployment '{existing_port.name}'",
            )

    # Automatically construct default base_url if not provided
    if not create_dict.get("base_url"):
        create_dict["base_url"] = f"http://localhost:{create_dict['port']}/v1"

    deployment = await deployment_repository.create(db, create_dict)
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


@router.post("/{deployment_id}/start", response_model=APIResponse[DeploymentResponse])
async def start_deployment(
    deployment_id: str,
    db: AsyncSession = Depends(get_db),
) -> APIResponse[DeploymentResponse]:
    """Start serving inference instance."""
    deployment = await deployment_repository.get_with_model(db, deployment_id)
    if not deployment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deployment with ID '{deployment_id}' not found",
        )

    if deployment.status == "running":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Deployment is already running",
        )

    started = await start_deployment_lifecycle(db, deployment)
    loaded = await deployment_repository.get_with_model(db, started.id)
    return APIResponse[DeploymentResponse](
        success=True,
        data=DeploymentResponse.model_validate(loaded or started),
        correlation_id=get_correlation_id(),
    )


@router.post("/{deployment_id}/stop", response_model=APIResponse[DeploymentResponse])
async def stop_deployment(
    deployment_id: str,
    db: AsyncSession = Depends(get_db),
) -> APIResponse[DeploymentResponse]:
    """Stop serving inference instance."""
    deployment = await deployment_repository.get_with_model(db, deployment_id)
    if not deployment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deployment with ID '{deployment_id}' not found",
        )

    if deployment.status == "stopped":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Deployment is already stopped",
        )

    stopped = await stop_deployment_lifecycle(db, deployment)
    loaded = await deployment_repository.get_with_model(db, stopped.id)
    return APIResponse[DeploymentResponse](
        success=True,
        data=DeploymentResponse.model_validate(loaded or stopped),
        correlation_id=get_correlation_id(),
    )


@router.post("/{deployment_id}/restart", response_model=APIResponse[DeploymentResponse])
async def restart_deployment(
    deployment_id: str,
    db: AsyncSession = Depends(get_db),
) -> APIResponse[DeploymentResponse]:
    """Restart serving inference instance."""
    deployment = await deployment_repository.get_with_model(db, deployment_id)
    if not deployment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deployment with ID '{deployment_id}' not found",
        )

    restarted = await restart_deployment_lifecycle(db, deployment)
    loaded = await deployment_repository.get_with_model(db, restarted.id)
    return APIResponse[DeploymentResponse](
        success=True,
        data=DeploymentResponse.model_validate(loaded or restarted),
        correlation_id=get_correlation_id(),
    )


@router.get("/{deployment_id}/logs", response_model=APIResponse[DeploymentLogsResponse])
async def get_logs(
    deployment_id: str,
    db: AsyncSession = Depends(get_db),
) -> APIResponse[DeploymentLogsResponse]:
    """Retrieve runtime engine stdout/stderr log stream."""
    deployment = await deployment_repository.get(db, deployment_id)
    if not deployment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deployment with ID '{deployment_id}' not found",
        )

    logs = get_deployment_logs(deployment_id)
    return APIResponse[DeploymentLogsResponse](
        success=True,
        data=DeploymentLogsResponse(
            deployment_id=deployment_id,
            logs=[DeploymentLogEntry(**log) for log in logs],
            total_lines=len(logs),
        ),
        correlation_id=get_correlation_id(),
    )


@router.get("/{deployment_id}/health", response_model=APIResponse[DeploymentHealthProbeResponse])
async def probe_health(
    deployment_id: str,
    db: AsyncSession = Depends(get_db),
) -> APIResponse[DeploymentHealthProbeResponse]:
    """Check responsiveness and operational health of a deployment endpoint."""
    deployment = await deployment_repository.get(db, deployment_id)
    if not deployment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deployment with ID '{deployment_id}' not found",
        )

    health_data = await probe_deployment_health(deployment)
    return APIResponse[DeploymentHealthProbeResponse](
        success=True,
        data=DeploymentHealthProbeResponse(**health_data),
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
