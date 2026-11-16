"""Tests for Redis Asynchronous Connection Pool and Health Probes."""

from unittest.mock import AsyncMock, patch

import pytest

from backend.app.core.redis import (
    check_redis_health,
    close_redis_pool,
    get_redis_client,
    get_redis_pool,
)


@pytest.mark.asyncio
async def test_redis_pool_singleton():
    """Verify Redis pool initializes and returns a persistent singleton."""
    pool1 = get_redis_pool()
    pool2 = get_redis_pool()
    assert pool1 is pool2

    client = get_redis_client()
    assert client is not None
    await client.aclose()


@pytest.mark.asyncio
async def test_redis_health_probe_success():
    """Verify check_redis_health returns True when Redis ping succeeds."""
    with patch("redis.asyncio.Redis.ping", new_callable=AsyncMock) as mock_ping:
        mock_ping.return_value = True
        is_healthy = await check_redis_health()
        assert is_healthy is True


@pytest.mark.asyncio
async def test_redis_health_probe_failure():
    """Verify check_redis_health gracefully returns False when Redis ping raises ConnectionError."""
    with patch("redis.asyncio.Redis.ping", new_callable=AsyncMock) as mock_ping:
        mock_ping.side_effect = ConnectionRefusedError("Redis connection refused")
        is_healthy = await check_redis_health()
        assert is_healthy is False
