"""Adversarial RBAC & JWT manipulation tests (stubs).

Prerequisites:
- PostgreSQL with RLS enabled
- Kong gateway running with JWT plugin
- Test JWT tokens for tenant_a and tenant_b
"""

import pytest

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skip(reason="Requires Kong + PostgreSQL with seed data"),
]

TENANT_A_JWT = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyX2Ei..."
TENANT_B_JWT = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyX2Ii..."


class TestAdversarialRBAC:
    async def test_cross_tenant_mo_injection(self, async_client):
        pytest.skip("Implement: POST /api/v1/demand/queue with Tenant B's mo_id")

    async def test_cross_tenant_resolution_approval(self, async_client):
        pytest.skip("Implement: POST /api/v1/resolution/approve with Tenant B's scenario_id")

    async def test_jwt_tampered_tenant_id(self, async_client):
        pytest.skip("Implement: inject tampered JWT with forged tenant_id")

    async def test_jwt_expired_token_rejected(self, async_client):
        pytest.skip("Implement: send request with expired JWT")

    async def test_role_escalation_planner_to_admin(self, async_client):
        pytest.skip("Implement: POST /api/v1/admin/system-config with planner JWT")

    async def test_missing_jwt_returns_401(self, async_client):
        pytest.skip("Implement: request without Authorization header via Kong upstream")
