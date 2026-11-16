"""Correlation ID and Request Timing Middleware for InferX."""

import time
import uuid
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from backend.app.core.logging import set_correlation_id


class CorrelationMiddleware(BaseHTTPMiddleware):
    """Ensures every request has a correlation ID and records response execution latency."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Check client header or generate new UUID
        correlation_id = (
            request.headers.get("X-Request-ID")
            or request.headers.get("X-Correlation-ID")
            or uuid.uuid4().hex
        )

        set_correlation_id(correlation_id)
        request.state.correlation_id = correlation_id

        start_time = time.perf_counter()
        response: Response = await call_next(request)
        process_time_ms = (time.perf_counter() - start_time) * 1000.0

        # Inject telemetry headers into response
        response.headers["X-Request-ID"] = correlation_id
        response.headers["X-Response-Time"] = f"{process_time_ms:.2f}ms"

        return response
