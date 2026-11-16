"""Pytest Fixtures and Test Harness for InferX Backend."""

import os
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

# Set test environment flag before loading app
os.environ["APP_ENV"] = "testing"

from backend.app.main import app


@pytest.fixture(scope="session")
def sync_client() -> Generator[TestClient, None, None]:
    """Synchronous test client fixture."""
    with TestClient(app=app, base_url="http://testserver") as client:
        yield client


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Asynchronous HTTP test client fixture."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client
