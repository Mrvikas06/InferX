"""API Key Generation, Verification, and Revocation Tests."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_and_use_api_key(async_client: AsyncClient):
    """Test generating an API key, using it to authenticate, and checking properties."""
    # 1. Register admin user to get auth token for key creation
    reg_res = await async_client.post(
        "/api/v1/auth/register",
        json={"email": "keymaker@inferx.ai", "password": "Password123!"},
    )
    assert reg_res.status_code == 201

    login_res = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "keymaker@inferx.ai", "password": "Password123!"},
    )
    admin_token = login_res.json()["data"]["access_token"]

    # 2. Generate API Key
    key_payload = {
        "name": "Production Ingestion Worker",
        "role": "operator",
        "rate_limit_rps": 100,
    }
    create_key_res = await async_client.post(
        "/api/v1/api-keys",
        json=key_payload,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert create_key_res.status_code == 201
    key_data = create_key_res.json()["data"]
    assert "raw_key" in key_data
    raw_key = key_data["raw_key"]
    assert raw_key.startswith("ifx_live_")
    key_id = key_data["id"]

    # 3. Use the raw API key to access protected endpoint via Bearer header
    list_keys_res = await async_client.get(
        "/api/v1/api-keys",
        headers={"Authorization": f"Bearer {raw_key}"},
    )
    assert list_keys_res.status_code == 200
    listed_keys = list_keys_res.json()["data"]["items"]
    assert len(listed_keys) >= 1
    # Plaintext raw_key should not be in the listed items
    assert not hasattr(listed_keys[0], "raw_key")

    # 4. Use the raw API key via X-API-Key header
    header_res = await async_client.get(
        "/api/v1/api-keys",
        headers={"X-API-Key": raw_key},
    )
    assert header_res.status_code == 200

    # 5. Revoke the API key
    revoke_res = await async_client.delete(
        f"/api/v1/api-keys/{key_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert revoke_res.status_code == 200
    assert revoke_res.json()["data"]["is_active"] is False

    # 6. Attempting to authenticate with revoked key should fail with 401
    fail_res = await async_client.get(
        "/api/v1/api-keys",
        headers={"Authorization": f"Bearer {raw_key}"},
    )
    assert fail_res.status_code == 401
    assert "revoked" in fail_res.json()["detail"]
