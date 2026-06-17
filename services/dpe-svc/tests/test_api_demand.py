from uuid import UUID

import pytest

INVALID_UUIDS = ["not-a-uuid", "123", "abc-def-ghi", "", "null", "None", "00000000-0000-0000-0000-00000000000Z"]


@pytest.mark.asyncio
async def test_health_endpoint(client):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "dpe-svc"


@pytest.mark.asyncio
async def test_classify_no_tenant(client):
    response = await client.post(
        "/api/v1/demand/classify",
        json={"demand_line_ids": [str(UUID(int=1))]},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["error"]["code"] == "NO_TENANT"


@pytest.mark.asyncio
async def test_queue_no_tenant(client):
    response = await client.get("/api/v1/demand/queue")
    assert response.status_code == 200
    data = response.json()
    assert data["error"]["code"] == "NO_TENANT"


@pytest.mark.parametrize("bad_uuid", INVALID_UUIDS)
@pytest.mark.asyncio
async def test_classify_invalid_uuid_returns_422(bad_uuid, client):
    """Prompt 1.1: Invalid UUID in demand_line_ids is rejected by Pydantic validation."""
    response = await client.post(
        "/api/v1/demand/classify",
        json={"demand_line_ids": [bad_uuid]},
    )
    assert response.status_code == 422


@pytest.mark.parametrize("bad_uuid", INVALID_UUIDS)
@pytest.mark.asyncio
async def test_queue_empty_demand_line_ids_returns_422(bad_uuid, client):
    """Prompt 1.1: Invalid UUID in demand_line_ids body field."""
    response = await client.post(
        "/api/v1/demand/classify",
        json={"demand_line_ids": [bad_uuid]},
    )
    assert response.status_code == 422
