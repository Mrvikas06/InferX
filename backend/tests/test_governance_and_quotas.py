"""Tests for Enterprise Governance, Token Quota Policies, and Audit Compliance Exports."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.deployment import Deployment
from backend.app.models.model import Model
from backend.app.models.quota import QuotaPolicy
from backend.app.repositories.audit_log_repository import audit_log_repository
from backend.app.repositories.quota_repository import quota_repository
from backend.app.schemas.quota import QuotaPolicyCreate, QuotaPolicyUpdate


@pytest.mark.asyncio
async def test_quota_repository_lifecycle(db_session: AsyncSession):
    """Test quota policy creation, token consumption recording, and budget exhaustion."""
    # 1. Create Policy
    create_payload = QuotaPolicyCreate(
        name="Test Dev Tier",
        target_type="user",
        target_id="test-usr-123",
        max_tokens_per_day=5000,
        max_tokens_per_month=50000,
        rate_limit_rpm=60,
        is_active=True,
    )
    policy = await quota_repository.create(db_session, create_payload)
    assert policy.id is not None
    assert policy.name == "Test Dev Tier"

    # 2. Check quota when clean
    allowed, reason, remaining = await quota_repository.check_quota(
        db_session, target_type="user", target_id="test-usr-123", estimated_tokens=100
    )
    assert allowed is True
    assert remaining == 5000

    # 3. Record consumption of 3000 tokens
    updated = await quota_repository.record_consumption(
        db_session, target_type="user", target_id="test-usr-123", tokens_consumed=3000
    )
    assert updated is not None
    assert updated.used_tokens_today == 3000
    assert updated.total_requests_count == 1

    # 4. Check remaining quota
    allowed, reason, remaining = await quota_repository.check_quota(
        db_session, target_type="user", target_id="test-usr-123", estimated_tokens=1000
    )
    assert allowed is True
    assert remaining == 2000

    # 5. Attempt request exceeding remaining daily budget (needs 2500, only 2000 left)
    allowed, reason, remaining = await quota_repository.check_quota(
        db_session, target_type="user", target_id="test-usr-123", estimated_tokens=2500
    )
    assert allowed is False
    assert "Daily token quota exceeded" in reason


@pytest.mark.asyncio
async def test_governance_api_crud(
    async_client: AsyncClient,
    db_session: AsyncSession,
):
    """Test Governance API endpoints for managing quotas."""
    # Register/login admin user
    await async_client.post(
        "/api/v1/auth/register",
        json={"email": "govadmin@inferx.ai", "password": "Password123!"},
    )
    login_resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "govadmin@inferx.ai", "password": "Password123!"},
    )
    admin_token = login_resp.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Create Quota Policy via API
    create_payload = {
        "name": "Org Alpha Quota",
        "target_type": "tenant",
        "target_id": "tenant-alpha",
        "max_tokens_per_day": 500000,
        "max_tokens_per_month": 10000000,
        "rate_limit_rpm": 300,
        "is_active": True,
    }
    create_resp = await async_client.post(
        "/api/v1/governance/quotas",
        json=create_payload,
        headers=headers,
    )
    assert create_resp.status_code == 201
    created_data = create_resp.json()["data"]
    policy_id = created_data["id"]
    assert created_data["name"] == "Org Alpha Quota"

    # 2. List Quotas
    list_resp = await async_client.get(
        "/api/v1/governance/quotas",
        headers=headers,
    )
    assert list_resp.status_code == 200
    assert list_resp.json()["data"]["total"] >= 1

    # 3. Get Usage Summary
    usage_resp = await async_client.get(
        f"/api/v1/governance/quotas/{policy_id}/usage",
        headers=headers,
    )
    assert usage_resp.status_code == 200
    usage_data = usage_resp.json()["data"]
    assert usage_data["daily_quota"] == 500000
    assert usage_data["daily_remaining"] == 500000
    assert usage_data["is_exhausted"] is False

    # 4. Update Policy
    update_resp = await async_client.put(
        f"/api/v1/governance/quotas/{policy_id}",
        json={"max_tokens_per_day": 750000},
        headers=headers,
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["data"]["max_tokens_per_day"] == 750000

    # 5. Reset Counters
    reset_resp = await async_client.post(
        f"/api/v1/governance/quotas/{policy_id}/reset",
        headers=headers,
    )
    assert reset_resp.status_code == 200
    assert reset_resp.json()["data"]["daily_used"] == 0

    # 6. Delete Policy
    del_resp = await async_client.delete(
        f"/api/v1/governance/quotas/{policy_id}",
        headers=headers,
    )
    assert del_resp.status_code == 200


@pytest.mark.asyncio
async def test_audit_logs_compliance_export(
    async_client: AsyncClient,
    db_session: AsyncSession,
):
    """Test streaming CSV and JSON exports for compliance auditing."""
    # Insert sample audit entries
    await audit_log_repository.record(
        db=db_session,
        action="compliance.test_action",
        resource_type="deployment",
        resource_id="dep-compliance-1",
        actor_id="actor-test-1",
        status="success",
        details={"audit": "passed"},
        ip_address="10.0.0.1",
    )
    await db_session.commit()

    # 1. Export CSV
    csv_resp = await async_client.get("/api/v1/audit-logs/export?format=csv")
    assert csv_resp.status_code == 200
    assert "text/csv" in csv_resp.headers["content-type"]
    assert "inferx-audit-logs.csv" in csv_resp.headers.get("content-disposition", "")
    assert "action" in csv_resp.text
    assert "compliance.test_action" in csv_resp.text

    # 2. Export JSON
    json_resp = await async_client.get("/api/v1/audit-logs/export?format=json")
    assert json_resp.status_code == 200
    assert "application/json" in json_resp.headers["content-type"]
    logs_array = json_resp.json()
    assert isinstance(logs_array, list)
    assert any(entry["action"] == "compliance.test_action" for entry in logs_array)
