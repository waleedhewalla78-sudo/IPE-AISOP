from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest

from ipe_shared.middleware.tenant_context import tenant_ctx

DEMO_TENANT = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"
DEMO_USER = "c0eebc99-9c0b-4ef8-bb6d-6bb9bd380c03"


def test_copilot_session_fk_metadata_resolves():
    from ipe_shared.models.user import User  # noqa: F401
    from ipe_shared.models.v8_planning import CopilotSession

    fk = next(iter(CopilotSession.__table__.c.user_id.foreign_keys))
    assert fk.column.table.name == User.__tablename__


@pytest.mark.asyncio
async def test_copilot_agents(client, auth_headers):
    token = tenant_ctx.set(DEMO_TENANT)
    try:
        response = await client.get("/api/v1/copilot/agents", headers=auth_headers)
        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        roles = [agent["role"] for agent in body["data"]["agents"]]
        assert "planner" in roles
    finally:
        tenant_ctx.reset(token)


@pytest.mark.asyncio
async def test_copilot_create_session():
    from httpx import ASGITransport, AsyncClient

    from app.main import create_app
    from ipe_shared.testing.conftest_helpers import (
        apply_v8_api_overrides,
        clear_overrides,
        make_auth_headers,
    )

    app = create_app()
    apply_v8_api_overrides(app, role="planner")
    headers = make_auth_headers(
        role="planner",
        tenant_id=UUID(DEMO_TENANT),
        user_id=UUID(DEMO_USER),
    )
    token = tenant_ctx.set(DEMO_TENANT)
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/copilot/session",
                json={"role": "planner"},
                headers=headers,
            )
            assert response.status_code == 200
            body = response.json()
            assert body["success"] is True
            assert body["data"]["role"] == "planner"
            assert body["data"]["session_id"]
    finally:
        tenant_ctx.reset(token)
        clear_overrides(app)


@pytest.mark.asyncio
async def test_health_endpoint(client):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["service"] == "nlp-svc"


@pytest.mark.asyncio
async def test_query_no_tenant(client):
    response = await client.post("/api/v1/copilot/query", json={"query": "hello"})
    assert response.status_code == 200
    assert response.json()["error"]["code"] == "NO_TENANT"


@pytest.mark.asyncio
async def test_query_with_tenant_and_mocked_llm(client, auth_headers):
    mock_fetcher = AsyncMock(return_value="")
    token = tenant_ctx.set("a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11")
    try:
        with patch("app.core.orchestrator._classify_intent", return_value="general"), \
             patch("app.core.orchestrator._INTENT_DATA_FETCHERS", {"general": mock_fetcher}), \
             patch("app.core.orchestrator.query_llm", return_value="Mock response"), \
             patch("app.api.v1.copilot.kafka_producer") as mock_kp:
            mock_kp.send_event = AsyncMock()
            mock_kp.build_envelope = MagicMock(return_value=MagicMock(model_dump=MagicMock(return_value={})))
            mock_kp.send_avro = AsyncMock()
            response = await client.post(
                "/api/v1/copilot/query",
                json={"query": "what is my production status?"},
                headers=auth_headers,
            )
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["intent"] == "general"
            assert data["data"]["response"] == "Mock response"
            assert "nlp-svc:general" in data["data"]["sources"]
    finally:
        tenant_ctx.reset(token)


@pytest.mark.asyncio
async def test_unauthorized_access_returns_401(rbac_client):
    response = await rbac_client.post("/api/v1/copilot/query", json={"query": "hello"})
    assert response.status_code == 401
