"""Tests for multi-tenant ops dashboard API (Sprint S8)."""

import os
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://ipe:ipe_dev_pass@localhost:5432/ipe_dev")
os.environ.setdefault("REDIS_URL", "redis://localhost:6380/0")
os.environ.setdefault("IPE_JWT_SIGNING_MODE", "hs256")
os.environ.setdefault("IPE_JWT_SECRET_KEY", "dev-jwt-secret-change-in-production-min-32-chars")
os.environ.setdefault("OTEL_SDK_DISABLED", "true")

from ipe_shared.database.session import get_session
from ipe_shared.testing.conftest_helpers import make_auth_headers


@pytest.mark.asyncio
async def test_tenant_health_requires_admin(rbac_client):
    resp = await rbac_client.get(
        "/api/v1/ops/tenants/health",
        headers=make_auth_headers(role="planner"),
    )
    assert resp.status_code in (401, 403)


@pytest.mark.asyncio
async def test_tenant_health_returns_summary():
    tenant = SimpleNamespace(
        id=uuid4(),
        name="Acme Mfg",
        tier="professional",
        erp_type="odoo",
        is_active=True,
    )

    async def mock_execute(stmt):
        stmt_str = str(stmt).lower()

        class Result:
            def scalars(self):
                return self

            def scalar_one_or_none(self):
                return None

            def scalar(self):
                return 0

            def all(self):
                return []

        if "cdm_tenant" in stmt_str and "cdm_sync_run" not in stmt_str:
            return SimpleNamespace(scalars=lambda: SimpleNamespace(all=lambda: [tenant]))
        return Result()

    session = AsyncMock()
    session.execute = mock_execute
    session.commit = AsyncMock()
    session.add = lambda *a, **k: None

    from app.main import create_app
    from ipe_shared.testing.conftest_helpers import apply_auth_and_session_overrides

    app = create_app()
    apply_auth_and_session_overrides(app)
    app.dependency_overrides[get_session] = lambda: session

    from httpx import ASGITransport, AsyncClient

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(
            "/api/v1/ops/tenants/health",
            headers=make_auth_headers(role="admin"),
        )

    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["data"]["summary"]["total"] == 1


@pytest.mark.asyncio
async def test_tenant_alerts_returns_list(client):
    resp = await client.get(
        "/api/v1/ops/tenants/alerts",
        headers=make_auth_headers(role="admin"),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert "alerts" in body["data"]
