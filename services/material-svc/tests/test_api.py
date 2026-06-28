import pytest


@pytest.mark.asyncio
async def test_health(client):
    r = await client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json()["service"] == "material-svc"


@pytest.mark.asyncio
async def test_list_materials(client, auth_headers):
    r = await client.get("/api/v1/materials", headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert body["data"]["count"] >= 1


@pytest.mark.asyncio
async def test_design_recommend(client, auth_headers):
    r = await client.post(
        "/api/v1/design/recommend",
        json={"required_tensile_mpa": 250, "max_cost_per_kg": 5},
        headers=auth_headers,
    )
    assert r.status_code == 200
    assert len(r.json()["data"]["recommendations"]) >= 1


@pytest.mark.asyncio
async def test_design_compliance(client, auth_headers):
    r = await client.post(
        "/api/v1/design/check-compliance",
        json={"process_type": "machining", "parameters": {"max_hardness_hrc": 40}},
        headers=auth_headers,
    )
    assert r.status_code == 200
    assert r.json()["data"]["compliant"] is True
