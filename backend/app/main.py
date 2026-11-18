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
from fastapi.responses import JSONResponse, PlainTextResponse

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

    # 7. Prometheus Metrics Scrape Endpoint
    @app.get("/metrics", response_class=PlainTextResponse, tags=["Observability"])
    async def prometheus_metrics() -> str:
        """Expose Prometheus formatted metric series for scraping."""
        try:
            from backend.app.services.gpu_monitor import get_gpu_telemetry
            from backend.app.services.load_balancer import load_balancer
            from backend.app.services.telemetry_service import telemetry_service
        except ImportError:
            from app.services.gpu_monitor import get_gpu_telemetry
            from app.services.load_balancer import load_balancer
            from app.services.telemetry_service import telemetry_service

        snapshot = telemetry_service.get_live_inference_snapshot()
        gpus = get_gpu_telemetry()
        cluster_stats = load_balancer.get_cluster_stats()
        active_reqs = cluster_stats.get("total_active_requests", 0)

        lines = [
            "# HELP inferx_active_requests Number of current in-flight inference requests",
            "# TYPE inferx_active_requests gauge",
            f"inferx_active_requests {active_reqs}",
            "# HELP inferx_requests_total Total number of inference requests processed",
            "# TYPE inferx_requests_total counter",
            f"inferx_requests_total {snapshot.total_requests}",
            "# HELP inferx_qps Current request throughput per second",
            "# TYPE inferx_qps gauge",
            f"inferx_qps {snapshot.qps:.2f}",
            "# HELP inferx_tokens_per_second Current token throughput per second",
            "# TYPE inferx_tokens_per_second gauge",
            f"inferx_tokens_per_second {snapshot.tokens_per_second:.2f}",
            "# HELP inferx_ttft_avg_ms Average time to first token in milliseconds",
            "# TYPE inferx_ttft_avg_ms gauge",
            f"inferx_ttft_avg_ms {snapshot.avg_ttft_ms:.2f}",
            "# HELP inferx_latency_p50_ms 50th percentile latency in milliseconds",
            "# TYPE inferx_latency_p50_ms gauge",
            f"inferx_latency_p50_ms {snapshot.latency_p50_ms:.2f}",
            "# HELP inferx_latency_p95_ms 95th percentile latency in milliseconds",
            "# TYPE inferx_latency_p95_ms gauge",
            f"inferx_latency_p95_ms {snapshot.latency_p95_ms:.2f}",
            "# HELP inferx_latency_p99_ms 99th percentile latency in milliseconds",
            "# TYPE inferx_latency_p99_ms gauge",
            f"inferx_latency_p99_ms {snapshot.latency_p99_ms:.2f}",
            "# HELP inferx_kv_cache_usage_percent Global KV-cache allocation percentage",
            "# TYPE inferx_kv_cache_usage_percent gauge",
            f"inferx_kv_cache_usage_percent {snapshot.kv_cache_usage_pct:.1f}",
            "# HELP inferx_active_deployments Number of running model deployments",
            "# TYPE inferx_active_deployments gauge",
            f"inferx_active_deployments {snapshot.active_deployments}",
        ]

        for gpu in gpus:
            temp = gpu.temperature_c if gpu.temperature_c is not None else 45.0
            lines.extend([
                f'inferx_gpu_utilization_percent{{gpu="{gpu.index}",name="{gpu.name}"}} {gpu.gpu_utilization_pct:.1f}',
                f'inferx_gpu_memory_used_mb{{gpu="{gpu.index}",name="{gpu.name}"}} {gpu.memory_used_mb:.1f}',
                f'inferx_gpu_memory_total_mb{{gpu="{gpu.index}",name="{gpu.name}"}} {gpu.memory_total_mb:.1f}',
                f'inferx_gpu_temperature_celsius{{gpu="{gpu.index}",name="{gpu.name}"}} {temp:.1f}',
            ])

        return "\n".join(lines) + "\n"

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
