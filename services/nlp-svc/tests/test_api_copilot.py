from unittest.mock import AsyncMock, patch

import pytest

from ipe_shared.middleware.tenant_context import tenant_ctx


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
async def test_query_with_tenant_and_mocked_llm(client):
    mock_fetcher = AsyncMock(return_value="")
    token = tenant_ctx.set("a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11")
    try:
        with patch("app.core.orchestrator._classify_intent", return_value="general"), \
             patch("app.core.orchestrator._INTENT_DATA_FETCHERS", {"general": mock_fetcher}), \
             patch("app.core.orchestrator.query_llm", return_value="Mock response"):
            response = await client.post(
                "/api/v1/copilot/query",
                json={"query": "what is my production status?"},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["intent"] == "general"
            assert data["data"]["response"] == "Mock response"
            assert "nlp-svc:general" in data["data"]["sources"]
    finally:
        tenant_ctx.reset(token)
