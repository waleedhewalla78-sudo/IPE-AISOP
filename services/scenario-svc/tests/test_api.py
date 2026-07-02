import pytest


@pytest.mark.asyncio
async def test_health(client):
    r = await client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json()["service"] == "scenario-svc"


@pytest.mark.asyncio
async def test_list_scenarios_empty(client, auth_headers):
    r = await client.get("/api/v1/scenario", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["data"]["scenarios"] == []


@pytest.mark.asyncio
async def test_create_and_get_scenario(client, auth_headers):
    create = await client.post(
        "/api/v1/scenario",
        json={"name": "QA baseline", "description": "validation"},
        headers=auth_headers,
    )
    assert create.status_code == 200
    sid = create.json()["data"]["scenario_id"]
    got = await client.get(f"/api/v1/scenario/{sid}", headers=auth_headers)
    assert got.status_code == 200
    assert got.json()["data"]["name"] == "QA baseline"


@pytest.mark.asyncio
async def test_simulate_scenario(client, auth_headers):
    create = await client.post(
        "/api/v1/scenario",
        json={"name": "Sim run"},
        headers=auth_headers,
    )
    sid = create.json()["data"]["scenario_id"]
    sim = await client.post(f"/api/v1/scenario/{sid}/simulate", headers=auth_headers)
    assert sim.status_code == 200
    assert sim.json()["success"] is True
