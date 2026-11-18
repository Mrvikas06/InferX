"""InferX Backend Control Plane — FastAPI Entrypoint."""

import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

# Bootstrap sys.path so InferX root is resolvable when main.py is run directly
_repo_root = str(Path(__file__).resolve().parent.parent.parent)
if _repo_root not in sys.path:
    sys.path.insert(0, _repo_root)

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.api.v1.health import router as health_router
from backend.app.api.v1.inference import router as inference_router
from backend.app.api.v1.router import api_v1_router
from backend.app.api.v1.schemas import APIResponse
from backend.app.core.config import get_settings
from backend.app.core.logging import get_correlation_id, setup_logging
from backend.app.core.redis import close_redis_pool
from backend.app.middleware.correlation import CorrelationMiddleware
from backend.app.middleware.security import SecurityHeadersMiddleware

settings = get_settings()
logger = logging.getLogger("inferx.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for initialization and graceful teardown."""
    # Initialize structured logging
    setup_logging(log_level=settings.LOG_LEVEL, log_format=settings.LOG_FORMAT)
    logger.info(
        "Starting %s v%s in [%s] environment",
        settings.APP_NAME,
        settings.VERSION,
        settings.APP_ENV,
    )
    logger.info("Control plane listening on %s:%d", settings.BACKEND_HOST, settings.BACKEND_PORT)

    # Auto-initialize SQLite schema if configured
    if "sqlite" in settings.DATABASE_URL:
        try:
            from backend.app.db.base import Base
            from backend.app.db.session import engine
            import backend.app.models  # noqa: F401
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("SQLite database schema initialized successfully")
        except Exception as exc:
            logger.warning("Could not auto-initialize SQLite schema: %s", exc)

    yield

    logger.info("Shutting down %s control plane gracefully", settings.APP_NAME)
    try:
        await close_redis_pool()
    except Exception as exc:
        logger.warning("Error closing Redis pool: %s", exc)


def create_app() -> FastAPI:
    """FastAPI application factory for InferX."""
    app = FastAPI(
        title=f"{settings.APP_NAME} Control Plane",
        description="Unified self-hosted LLM inference management, routing, benchmarking, and GPU telemetry platform.",
        version=settings.VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # 1. Correlation & Telemetry Middleware (runs first on request / last on response)
    app.add_middleware(CorrelationMiddleware)

    # 2. Production Security Hardening Headers Middleware
    app.add_middleware(SecurityHeadersMiddleware)

    # 2. CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-Response-Time"],
    )

    # 3. Global Exception Handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        correlation_id = get_correlation_id()
        logger.error("Unhandled exception processing request: %s", exc, exc_info=True)
        response_data = APIResponse[None](
            success=False,
            data=None,
            error=str(exc) if settings.DEBUG else "Internal server error",
            correlation_id=correlation_id,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=response_data.model_dump(mode="json"),
        )

    # 4. Root Health Endpoints (Accessible at root /health for AWS/GCP/K8s/Docker health checkers)
    app.include_router(health_router, prefix="", tags=["Root Health"])

    # 5. Versioned API Router
    app.include_router(api_v1_router, prefix="/api/v1")

    # 6. Direct OpenAI-Compatible Gateway Router (for standard SDKs with base_url="http://host:port/v1")
    app.include_router(inference_router, prefix="/v1", tags=["OpenAI Inference Gateway"])

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.app.main:app",
        host=settings.BACKEND_HOST,
        port=settings.BACKEND_PORT,
        reload=settings.is_development,
    )
