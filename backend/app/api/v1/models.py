"""Model Registry CRUD API Endpoints for InferX."""

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
    ModelListResponse,
    ModelResponse,
    ModelUpdate,
)

router = APIRouter()


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

    model = await model_repository.create(db, payload)
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
