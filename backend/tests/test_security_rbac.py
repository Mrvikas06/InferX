"""RBAC Permissions, Rate Limiting, and Audit Trail Tests."""

import pytest
from httpx import AsyncClient

from backend.app.core.rate_limit import check_rate_limit


@pytest.mark.asyncio
async def test_rbac_permission_boundaries(async_client: AsyncClient):
    """Verify viewer cannot execute operator/admin actions, and operator cannot access admin audit logs."""
    # 1. First user registered is admin
    await async_client.post(
        "/api/v1/auth/register",
        json={"email": "superadmin@inferx.ai", "password": "Password123!"},
    )
    admin_login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "superadmin@inferx.ai", "password": "Password123!"},
    )
    admin_token = admin_login.json()["data"]["access_token"]

    # 2. Second user is viewer
    await async_client.post(
        "/api/v1/auth/register",
        json={"email": "viewer@inferx.ai", "password": "Password123!", "role": "viewer"},
    )
    viewer_login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "viewer@inferx.ai", "password": "Password123!"},
    )
    viewer_token = viewer_login.json()["data"]["access_token"]

    # 3. Third user is operator
    await async_client.post(
        "/api/v1/auth/register",
        json={"email": "operator@inferx.ai", "password": "Password123!", "role": "operator"},
    )
    operator_login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "operator@inferx.ai", "password": "Password123!"},
    )
    operator_token = operator_login.json()["data"]["access_token"]

    # Viewer attempts operator action (create API key) -> 403 Forbidden
    viewer_fail = await async_client.post(
        "/api/v1/api-keys",
        json={"name": "Viewer Key Attempt"},
        headers={"Authorization": f"Bearer {viewer_token}"},
    )
    assert viewer_fail.status_code == 403
    assert "requires 'operator' role" in viewer_fail.json()["detail"]

    # Operator creates API key -> 201 Created
    op_success = await async_client.post(
        "/api/v1/api-keys",
        json={"name": "Operator Valid Key"},
        headers={"Authorization": f"Bearer {operator_token}"},
    )
    assert op_success.status_code == 201

    # Operator attempts admin action (view audit logs) -> 403 Forbidden
    op_audit_fail = await async_client.get(
        "/api/v1/audit-logs",
        headers={"Authorization": f"Bearer {operator_token}"},
    )
    assert op_audit_fail.status_code == 403
    assert "requires 'admin' role" in op_audit_fail.json()["detail"]

    # Admin accesses audit logs -> 200 OK
    admin_audit = await async_client.get(
        "/api/v1/audit-logs",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert admin_audit.status_code == 200
    logs = admin_audit.json()["data"]["items"]
    assert len(logs) >= 3  # Multiple registrations and logins have been logged


@pytest.mark.asyncio
async def test_sliding_window_rate_limiter():
    """Verify check_rate_limit enforces sliding-window rate ceiling."""
    identifier = "test-client-unique-id"
    # Limit: 3 requests per 1 second
    allowed_1, rem_1, _ = await check_rate_limit(identifier, max_requests=3, window_seconds=1)
    allowed_2, rem_2, _ = await check_rate_limit(identifier, max_requests=3, window_seconds=1)
    allowed_3, rem_3, _ = await check_rate_limit(identifier, max_requests=3, window_seconds=1)
    allowed_4, rem_4, _ = await check_rate_limit(identifier, max_requests=3, window_seconds=1)

    assert allowed_1 is True
    assert allowed_2 is True
    assert allowed_3 is True
    assert allowed_4 is False
    assert rem_4 == 0
