"""API v1 Router aggregating modular subrouters for InferX."""

from fastapi import APIRouter

from backend.app.api.v1.api_keys import router as api_keys_router
from backend.app.api.v1.audit_logs import router as audit_logs_router
from backend.app.api.v1.auth import router as auth_router
from backend.app.api.v1.deployments import router as deployments_router
from backend.app.api.v1.health import router as health_router
from backend.app.api.v1.models import router as models_router

api_v1_router = APIRouter()

# Mount health and system endpoints
api_v1_router.include_router(health_router, prefix="", tags=["Health & System"])

# Mount Authentication & Identity endpoints
api_v1_router.include_router(auth_router, prefix="/auth", tags=["Authentication & Identity"])

# Mount API Key Management endpoints
api_v1_router.include_router(api_keys_router, prefix="/api-keys", tags=["API Keys"])

# Mount Security Audit Log endpoints
api_v1_router.include_router(audit_logs_router, prefix="/audit-logs", tags=["Audit Logs"])

# Mount Model Registry endpoints
api_v1_router.include_router(models_router, prefix="/models", tags=["Model Registry"])

# Mount Deployment Management endpoints
api_v1_router.include_router(deployments_router, prefix="/deployments", tags=["Deployment Management"])
