"""Model Registry CRUD and Deep Inspection API Endpoints for InferX."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.v1.schemas import APIResponse
from backend.app.core.logging import get_correlation_id
from backend.app.db.session import get_db
from backend.app.repositories.deployment_repository import deployment_repository
from backend.app.repositories.model_repository import model_repository
from backend.app.schemas.model import (
    ModelCreate,
    ModelInspectRequest,
    ModelInspectResponse,
    ModelListResponse,
    ModelResponse,
    ModelUpdate,
)
from backend.app.services.model_downloader import register_local_weights
from backend.app.services.model_inspector import (
    calculate_min_vram_gb,
    inspect_huggingface_repo,
)

router = APIRouter()


@router.post("/inspect", response_model=APIResponse[ModelInspectResponse])
async def inspect_model(
    payload: ModelInspectRequest,
) -> APIResponse[ModelInspectResponse]:
    """Inspect a HuggingFace model repository to detect architecture, parameters, and VRAM needs."""
    metadata = await inspect_huggingface_repo(payload.repo_id)
    return APIResponse[ModelInspectResponse](
        success=True,
        data=ModelInspectResponse(**metadata),
        correlation_id=get_correlation_id(),
    )


@router.get("", response_model=APIResponse[ModelListResponse])
async def list_models(
    query: Optional[str] = Query(None, description="Search keyword for name, repo_id, or architecture"),
    precision: Optional[str] = Query(None, description="Filter by precision (e.g. BF16, FP16, INT4)"),
    is_downloaded: Optional[bool] = Query(None, description="Filter by local cached state"),
    skip: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(20, ge=1, le=100, description="Page limit"),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[ModelListResponse]:
    """List and filter registered models with pagination."""
    items = await model_repository.search_models(
        db,
        query_str=query,
        precision=precision,
        is_downloaded=is_downloaded,
        skip=skip,
        limit=limit,
    )
    total = await model_repository.count_filtered(
        db,
        query_str=query,
        precision=precision,
        is_downloaded=is_downloaded,
    )
    return APIResponse[ModelListResponse](
        success=True,
        data=ModelListResponse(
            items=[ModelResponse.model_validate(m) for m in items],
            total=total,
            skip=skip,
            limit=limit,
        ),
        correlation_id=get_correlation_id(),
    )


@router.post("", response_model=APIResponse[ModelResponse], status_code=status.HTTP_201_CREATED)
async def register_model(
    payload: ModelCreate,
    db: AsyncSession = Depends(get_db),
) -> APIResponse[ModelResponse]:
    """Register a new LLM from HuggingFace repository ID or local weight path."""
    existing = await model_repository.get_by_repo_id(db, payload.repo_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Model with repo_id '{payload.repo_id}' is already registered (id: {existing.id})",
        )

    # Auto-calculate min_gpu_vram_gb if not provided
    create_dict = payload.model_dump()
    if create_dict.get("min_gpu_vram_gb") is None and create_dict.get("parameters") != "Unknown":
        create_dict["min_gpu_vram_gb"] = calculate_min_vram_gb(
            create_dict["parameters"],
            create_dict.get("precision", "BF16"),
            create_dict.get("context_window", 8192),
        )

    model = await model_repository.create(db, create_dict)
    return APIResponse[ModelResponse](
        success=True,
        data=ModelResponse.model_validate(model),
        correlation_id=get_correlation_id(),
    )


@router.get("/{model_id}", response_model=APIResponse[ModelResponse])
async def get_model(
    model_id: str,
    db: AsyncSession = Depends(get_db),
) -> APIResponse[ModelResponse]:
    """Retrieve detailed metadata for a registered model."""
    model = await model_repository.get(db, model_id)
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model with ID '{model_id}' not found",
        )
    return APIResponse[ModelResponse](
        success=True,
        data=ModelResponse.model_validate(model),
        correlation_id=get_correlation_id(),
    )


@router.patch("/{model_id}", response_model=APIResponse[ModelResponse])
async def update_model(
    model_id: str,
    payload: ModelUpdate,
    db: AsyncSession = Depends(get_db),
) -> APIResponse[ModelResponse]:
    """Partially update metadata or cache status of a registered model."""
    model = await model_repository.get(db, model_id)
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model with ID '{model_id}' not found",
        )

    updated_model = await model_repository.update(db, model, payload)
    return APIResponse[ModelResponse](
        success=True,
        data=ModelResponse.model_validate(updated_model),
        correlation_id=get_correlation_id(),
    )


@router.post("/{model_id}/verify-weights", response_model=APIResponse[ModelResponse])
async def verify_model_weights(
    model_id: str,
    db: AsyncSession = Depends(get_db),
) -> APIResponse[ModelResponse]:
    """Probe the local disk cache to verify model weights presence and calculate disk size."""
    model = await model_repository.get(db, model_id)
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model with ID '{model_id}' not found",
        )

    weight_info = register_local_weights(model.repo_id, model.local_path)
    model.is_downloaded = weight_info["is_downloaded"]
    model.local_path = weight_info["local_path"]
    if weight_info["size_on_disk_gb"] is not None:
        model.size_on_disk_gb = weight_info["size_on_disk_gb"]

    db.add(model)
    await db.flush()
    await db.refresh(model)

    return APIResponse[ModelResponse](
        success=True,
        data=ModelResponse.model_validate(model),
        correlation_id=get_correlation_id(),
    )


@router.delete("/{model_id}", response_model=APIResponse[ModelResponse])
async def delete_model(
    model_id: str,
    db: AsyncSession = Depends(get_db),
) -> APIResponse[ModelResponse]:
    """Unregister and remove a model from the registry."""
    model = await model_repository.get(db, model_id)
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model with ID '{model_id}' not found",
        )

    # Check for attached deployments
    deployments = await deployment_repository.get_by_model_id(db, model_id)
    if deployments:
        active_count = len(deployments)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete model '{model.name}'. It is currently referenced by {active_count} deployment(s). Remove them first.",
        )

    deleted = await model_repository.delete(db, model_id)
    return APIResponse[ModelResponse](
        success=True,
        data=ModelResponse.model_validate(deleted),
        correlation_id=get_correlation_id(),
    )
