"""API v1 Router aggregating modular subrouters for InferX."""

from fastapi import APIRouter

from backend.app.api.v1.deployments import router as deployments_router
from backend.app.api.v1.health import router as health_router
from backend.app.api.v1.models import router as models_router

api_v1_router = APIRouter()

# Mount health and system endpoints
api_v1_router.include_router(health_router, prefix="", tags=["Health & System"])

# Mount Model Registry endpoints
api_v1_router.include_router(models_router, prefix="/models", tags=["Model Registry"])

# Mount Deployment Management endpoints
api_v1_router.include_router(deployments_router, prefix="/deployments", tags=["Deployment Management"])

