import pytest


@pytest.mark.asyncio
async def test_health_endpoint(client):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["service"] == "del-svc"


@pytest.mark.asyncio
async def test_classify_no_tenant(client):
    response = await client.post("/api/v1/delay/classify", json={"source_text": "test"})
    assert response.status_code == 200
    assert response.json()["error"]["code"] == "NO_TENANT"
