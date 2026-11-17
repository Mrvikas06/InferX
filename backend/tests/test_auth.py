"""Authentication Integration Tests for Registration, Login, and JWT Rotation."""

import pytest
from httpx import AsyncClient

from backend.app.core.security import verify_password


@pytest.mark.asyncio
async def test_user_registration_and_first_admin(async_client: AsyncClient):
    """Verify first registered user receives admin role automatically."""
    reg_payload = {
        "email": "admin@inferx.ai",
        "password": "SuperSecretPassword123!",
        "full_name": "Admin User",
    }
    res = await async_client.post("/api/v1/auth/register", json=reg_payload)
    assert res.status_code == 201
    data = res.json()["data"]
    assert data["email"] == "admin@inferx.ai"
    assert data["role"] == "admin"
    assert data["is_superuser"] is True
    assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_user_registration_duplicate_email(async_client: AsyncClient):
    """Verify duplicate email registration yields 409 Conflict."""
    payload = {
        "email": "dev@inferx.ai",
        "password": "Password123!",
        "full_name": "Dev User",
    }
    res1 = await async_client.post("/api/v1/auth/register", json=payload)
    assert res1.status_code == 201

    res2 = await async_client.post("/api/v1/auth/register", json=payload)
    assert res2.status_code == 409
    assert "already exists" in res2.json()["detail"]


@pytest.mark.asyncio
async def test_login_success_and_token_generation(async_client: AsyncClient):
    """Verify valid credentials return JWT access and refresh token pair."""
    # Register user
    await async_client.post(
        "/api/v1/auth/register",
        json={"email": "alice@inferx.ai", "password": "SecretPassword123!"},
    )

    # Login
    login_res = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "alice@inferx.ai", "password": "SecretPassword123!"},
    )
    assert login_res.status_code == 200
    token_data = login_res.json()["data"]
    assert "access_token" in token_data
    assert "refresh_token" in token_data
    assert token_data["token_type"] == "bearer"
    assert token_data["expires_in"] > 0


@pytest.mark.asyncio
async def test_login_invalid_password(async_client: AsyncClient):
    """Verify wrong password returns 401 Unauthorized."""
    await async_client.post(
        "/api/v1/auth/register",
        json={"email": "bob@inferx.ai", "password": "CorrectPassword123!"},
    )

    login_res = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "bob@inferx.ai", "password": "WrongPassword999!"},
    )
    assert login_res.status_code == 401
    assert "Incorrect email or password" in login_res.json()["detail"]


@pytest.mark.asyncio
async def test_token_refresh_rotation(async_client: AsyncClient):
    """Verify refresh token exchanges for a new token pair."""
    await async_client.post(
        "/api/v1/auth/register",
        json={"email": "charlie@inferx.ai", "password": "Password123!"},
    )

    login_res = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "charlie@inferx.ai", "password": "Password123!"},
    )
    refresh_token = login_res.json()["data"]["refresh_token"]

    # Exchange refresh token
    refresh_res = await async_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_res.status_code == 200
    new_tokens = refresh_res.json()["data"]
    assert "access_token" in new_tokens
    assert "refresh_token" in new_tokens
    assert new_tokens["access_token"] != login_res.json()["data"]["access_token"]


@pytest.mark.asyncio
async def test_get_current_user_me(async_client: AsyncClient):
    """Verify /me profile endpoint with JWT Authorization header."""
    await async_client.post(
        "/api/v1/auth/register",
        json={"email": "david@inferx.ai", "password": "Password123!", "full_name": "David Bowie"},
    )
    login_res = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "david@inferx.ai", "password": "Password123!"},
    )
    access_token = login_res.json()["data"]["access_token"]

    # Request /me
    me_res = await async_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert me_res.status_code == 200
    profile = me_res.json()["data"]
    assert profile["email"] == "david@inferx.ai"
    assert profile["full_name"] == "David Bowie"


@pytest.mark.asyncio
async def test_get_me_unauthorized(async_client: AsyncClient):
    """Verify /me returns 401 when no token is supplied."""
    me_res = await async_client.get("/api/v1/auth/me")
    assert me_res.status_code == 401
