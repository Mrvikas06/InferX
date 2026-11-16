"""API v1 Router aggregating modular subrouters for InferX."""

from fastapi import APIRouter

from backend.app.api.v1.health import router as health_router

api_v1_router = APIRouter()

# Mount health and system endpoints under v1
api_v1_router.include_router(health_router, prefix="", tags=["Health & System"])
