"""Asynchronous Redis Client and Cache Layer for InferX."""

import logging
from typing import AsyncGenerator, Optional

import redis.asyncio as aioredis
from redis.asyncio.connection import ConnectionPool

from backend.app.core.config import get_settings

logger = logging.getLogger("inferx.redis")
settings = get_settings()

_pool: Optional[ConnectionPool] = None


def get_redis_pool() -> ConnectionPool:
    """Return the global async Redis connection pool."""
    global _pool
    if _pool is None:
        _pool = ConnectionPool.from_url(
            settings.REDIS_URL,
            max_connections=20,
            decode_responses=True,
            socket_timeout=1.0,
            socket_connect_timeout=0.2,
        )
    return _pool


def get_redis_client() -> aioredis.Redis:
    """Instantiate a Redis client from the shared connection pool."""
    return aioredis.Redis(connection_pool=get_redis_pool())


async def get_redis() -> AsyncGenerator[aioredis.Redis, None]:
    """Dependency injection provider for Redis clients."""
    client = get_redis_client()
    try:
        yield client
    finally:
        await client.aclose()


async def check_redis_health() -> bool:
    """Execute a ping probe to verify Redis connectivity."""
    client = get_redis_client()
    try:
        pong = await client.ping()
        return bool(pong)
    except Exception as exc:
        logger.warning("Redis health probe failed: %s", exc)
        return False
    finally:
        await client.aclose()


async def close_redis_pool() -> None:
    """Gracefully close all connections in the pool."""
    global _pool
    if _pool is not None:
        await _pool.disconnect()
        _pool = None
