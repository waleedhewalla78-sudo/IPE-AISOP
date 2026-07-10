"""Sprint S4 — scenario simulator KPI deltas."""

import pytest

from app.core.simulator import DEFAULT_BASELINE, compare_scenarios, simulate_kpis


def test_supplier_delay_reduces_otd():
    baseline = simulate_kpis({})
    stressed = simulate_kpis({"supplier_delay_days": "10"})
    assert stressed["otd_pct"] < baseline["otd_pct"]


def test_capacity_reduction_raises_utilization():
    baseline = simulate_kpis({})
    reduced = simulate_kpis({"capacity_reduction_pct": "20%"})
    assert reduced["capacity_util_pct"] > baseline["capacity_util_pct"]


def test_demand_increase_raises_risk():
    kpis = simulate_kpis({"demand_change_pct": "25%"})
    assert kpis["orders_at_risk"] > DEFAULT_BASELINE["orders_at_risk"]


def test_compare_against_baseline():
    results = [
        DEFAULT_BASELINE,
        simulate_kpis({"demand_change_pct": "10%", "supplier_delay_days": "5", "capacity_reduction_pct": "5%"}),
    ]
    comparison = compare_scenarios(results, DEFAULT_BASELINE)
    assert comparison[1]["deltas"]["otd_pct"] < 0


@pytest.mark.asyncio
async def test_post_simulate_persist(client, auth_headers):
    r = await client.post(
        "/api/v1/scenario/simulate",
        json={
            "name": "R2 stress test",
            "demand_change_pct": "15%",
            "supplier_delay_days": "3",
            "capacity_reduction_pct": "10%",
            "persist": True,
        },
        headers=auth_headers,
    )
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert "scenario_id" in body["data"]
    assert body["data"]["deltas"]["orders_at_risk"] > 0


@pytest.mark.asyncio
async def test_post_simulate_dry_run(client, auth_headers):
    r = await client.post(
        "/api/v1/scenario/simulate",
        json={
            "demand_change_pct": "0%",
            "supplier_delay_days": "0",
            "capacity_reduction_pct": "0%",
            "persist": False,
        },
        headers=auth_headers,
    )
    assert r.status_code == 200
    body = r.json()
    assert body["data"]["kpis"]["otd_pct"] == DEFAULT_BASELINE["otd_pct"]


@pytest.mark.asyncio
async def test_list_and_get_scenario(client, auth_headers):
    create = await client.post(
        "/api/v1/scenario/simulate",
        json={"name": "List test", "persist": True},
        headers=auth_headers,
    )
    assert create.status_code == 200
    body = create.json()["data"]
    sid = body["scenario_id"]
    assert body["parameters"]["supplier_delay_days"] == "0"
    detail = await client.get(f"/api/v1/scenario/{sid}", headers=auth_headers)
    assert detail.status_code == 200
    assert detail.json()["data"]["name"] == "List test"
    listed = await client.get("/api/v1/scenario", headers=auth_headers)
    assert listed.status_code == 200
    assert "scenarios" in listed.json()["data"]
