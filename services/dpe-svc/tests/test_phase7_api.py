"""Phase 7 Deep Planning API smoke tests (ASGI in-process).

Drives the real FastAPI app (router + Pydantic models + handlers) — the same code
Kong proxies to. New endpoints sit under the existing planning-command Kong route.
"""

from uuid import UUID

import pytest

from ipe_shared.auth.jwt import create_access_token

TENANT = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"


@pytest.fixture
def auth_headers():
    token = create_access_token(user_id=UUID(TENANT), tenant_id=UUID(TENANT), role="planner")
    return {"Authorization": f"Bearer {token}", "X-Tenant-ID": TENANT}


@pytest.mark.asyncio
async def test_phase7_disciplines(client, auth_headers):
    resp = await client.get("/api/v1/planning-command/phase7/disciplines", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["phase"] == "7"
    assert len(data["disciplines"]) == 6


@pytest.mark.asyncio
async def test_horizons_endpoint(client, auth_headers):
    resp = await client.get("/api/v1/planning-command/horizons", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert set(data["horizons"].keys()) == {"strategic", "tactical", "operational"}


@pytest.mark.asyncio
async def test_horizons_cascade_up(client, auth_headers):
    resp = await client.post(
        "/api/v1/planning-command/horizons/cascade",
        json={"direction": "up", "capex_usd": 180000},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["direction"] == "up"
    assert data["board_decision_required"] is True


@pytest.mark.asyncio
async def test_sop_financial_endpoint(client, auth_headers):
    resp = await client.post(
        "/api/v1/planning-command/sop/financial", json={}, headers=auth_headers
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data["periods"]) == 3
    assert data["finance_alerts"]


@pytest.mark.asyncio
async def test_sop_portfolio_endpoint(client, auth_headers):
    resp = await client.post(
        "/api/v1/planning-command/sop/portfolio", json={}, headers=auth_headers
    )
    assert resp.status_code == 200
    ranking = resp.json()["data"]["ranking"]
    assert ranking[0]["rank"] == 1


@pytest.mark.asyncio
async def test_demand_decompose_endpoint(client, auth_headers):
    resp = await client.post(
        "/api/v1/planning-command/demand/decompose",
        json={"month": 10, "base": 20, "trend_per_month": 2},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "components" in data
    assert data["forecast_units"] > 0


@pytest.mark.asyncio
async def test_demand_npi_endpoint(client, auth_headers):
    resp = await client.post(
        "/api/v1/planning-command/demand/npi", json={"months": 6}, headers=auth_headers
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data["composite_forecast"]) == 6


@pytest.mark.asyncio
async def test_production_setup_sequence_endpoint(client, auth_headers):
    resp = await client.post(
        "/api/v1/planning-command/production/setup-sequence",
        json={"jobs": ["DT100", "PT500", "DT100", "DT250"]},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["savings_min"] >= 0


@pytest.mark.asyncio
async def test_production_make_or_buy_endpoint(client, auth_headers):
    resp = await client.post(
        "/api/v1/planning-command/production/make-or-buy",
        json={"current_utilisation_pct": 95, "bottleneck_threshold_pct": 90},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["decision"] == "buy"


@pytest.mark.asyncio
async def test_operations_oee_endpoint(client, auth_headers):
    resp = await client.post(
        "/api/v1/planning-command/operations/oee-programme", json={}, headers=auth_headers
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["target_oee_pct"] > 0


@pytest.mark.asyncio
async def test_operations_gemba_stub_flag(client, auth_headers):
    resp = await client.get("/api/v1/planning-command/operations/gemba", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["iot_live"] is False


@pytest.mark.asyncio
async def test_operations_andon_lifecycle(client, auth_headers):
    trig = await client.post(
        "/api/v1/planning-command/operations/andon",
        json={
            "color": "red",
            "work_centre": "WC-WND",
            "reported_by": "Mohamed",
            "message": "Breakdown",
        },
        headers=auth_headers,
    )
    assert trig.status_code == 200
    alert_id = trig.json()["data"]["id"]
    res = await client.post(
        f"/api/v1/planning-command/operations/andon/{alert_id}/resolve",
        json={"resolution": "Motor replaced"},
        headers=auth_headers,
    )
    assert res.status_code == 200
    assert res.json()["data"]["status"] == "resolved"


@pytest.mark.asyncio
async def test_operations_kpi_tree_endpoint(client, auth_headers):
    resp = await client.get("/api/v1/planning-command/operations/kpi-tree", headers=auth_headers)
    assert resp.status_code == 200
    assert "WC-WND" in resp.json()["data"]["attention_work_centres"]


@pytest.mark.asyncio
async def test_calendar_endpoint(client, auth_headers):
    resp = await client.get("/api/v1/planning-command/calendar", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["total_activities"] > 0
