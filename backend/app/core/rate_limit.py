"""Rate Limiting Engine with Redis Sliding Window and Local In-Memory Fallback."""

import time
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

from fastapi import HTTPException, Request, status

from backend.app.core.config import get_settings
from backend.app.core.redis import get_redis_client

settings = get_settings()

# In-memory sliding window fallback: key -> list of float timestamps
_local_rate_limit_cache: Dict[str, List[float]] = defaultdict(list)
_redis_offline_until: float = 0.0


def reset_rate_limits() -> None:
    """Clear in-memory rate limiting state (used primarily in test suites)."""
    global _local_rate_limit_cache
    _local_rate_limit_cache.clear()


async def check_rate_limit(
    identifier: str,
    max_requests: int = 50,
    window_seconds: int = 1,
) -> Tuple[bool, int, int]:
    """
    Check sliding-window rate limit for a client identifier.
    Returns (is_allowed, remaining_quota, reset_seconds).
    Uses Redis sliding-window if available; falls back to local in-memory window.
    """
    global _redis_offline_until
    now = time.time()
    window_start = now - window_seconds
    redis_key = f"ratelimit:{identifier}:{window_seconds}s"

    if now > _redis_offline_until:
        try:
            client = get_redis_client()
            pipe = client.pipeline()
            # Clean expired timestamps outside sliding window
            pipe.zremrangebyscore(redis_key, 0, window_start)
            # Add current timestamp
            pipe.zadd(redis_key, {str(now): now})
            # Count elements in window
            pipe.zcard(redis_key)
            # Set expire
            pipe.expire(redis_key, window_seconds * 2)
            results = await pipe.execute()
            await client.aclose()

            request_count = results[2]
            allowed = request_count <= max_requests
            remaining = max(0, max_requests - request_count)
            return allowed, remaining, window_seconds

        except Exception:
            # Mark Redis offline for 30s to avoid latency on fallback
            _redis_offline_until = now + 30.0

    # Fallback to high-performance in-memory sliding window
    timestamps = _local_rate_limit_cache[identifier]
    # Prune old timestamps
    _local_rate_limit_cache[identifier] = [t for t in timestamps if t > window_start]
    _local_rate_limit_cache[identifier].append(now)

    current_count = len(_local_rate_limit_cache[identifier])
    allowed = current_count <= max_requests
    remaining = max(0, max_requests - current_count)
    return allowed, remaining, window_seconds


class RateLimiter:
    """FastAPI Dependency for route-level rate limiting."""

    def __init__(self, rps: Optional[int] = None):
        self.rps = rps or settings.DEFAULT_RATE_LIMIT_RPS

    async def __call__(self, request: Request) -> None:
        # Rate limit by API Key if present, else by client IP
        auth_header = request.headers.get("Authorization", "")
        api_key_header = request.headers.get("X-API-Key", "")
        client_ip = request.client.host if request.client else "unknown"

        if api_key_header:
            identifier = f"key:{api_key_header[:16]}"
        elif auth_header.startswith("Bearer ifx_live_"):
            identifier = f"key:{auth_header[14:30]}"
        elif auth_header.startswith("Bearer "):
            identifier = f"jwt:{auth_header[7:25]}"
        else:
            identifier = f"ip:{client_ip}"

        allowed, remaining, reset_secs = await check_rate_limit(
            identifier=identifier,
            max_requests=self.rps,
            window_seconds=1,
        )

        # Inject rate limit telemetry headers into request state
        request.state.rate_limit_limit = self.rps
        request.state.rate_limit_remaining = remaining
        request.state.rate_limit_reset = reset_secs

        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded: {self.rps} requests/second allowance reached. Try again in {reset_secs}s.",
                headers={
                    "X-RateLimit-Limit": str(self.rps),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset_secs),
                    "Retry-After": str(reset_secs),
                },
            )
