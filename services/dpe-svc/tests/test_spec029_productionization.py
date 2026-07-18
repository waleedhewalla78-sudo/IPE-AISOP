"""Spec 029 productionization unit tests — stage-gate, Andon persist, plan persist."""

from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest

from app.core.phase5.plan_persist import save_mps_run, save_mrp_run
from app.core.phase7.andon_persist import persist_andon_alert, persist_andon_resolve
from app.core.phase7.sop_stage_gate import SopStageGateMachine, reset_default_gate
from ipe_shared.auth.jwt import create_access_token

TENANT = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"


@pytest.fixture
def auth_headers():
    token = create_access_token(user_id=UUID(TENANT), tenant_id=UUID(TENANT), role="planner")
    return {"Authorization": f"Bearer {token}", "X-Tenant-ID": TENANT}


def test_stage_gate_advance_and_skip():
    gate = SopStageGateMachine()
    assert gate.current_stage == "demand_review"
    snap = gate.advance(note="demand ok")
    assert snap["current_stage"] == "supply_review"
    assert snap["stages"][0]["status"] == "approved"
    skipped = gate.skip_to_management_review(note="urgent")
    assert skipped["current_stage"] == "management_review"
    assert any(s["status"] == "skipped" for s in skipped["stages"])


def test_stage_gate_reset_default():
    reset_default_gate()
    g = reset_default_gate()
    assert g.current_stage == "demand_review"


@pytest.mark.asyncio
async def test_persist_andon_alert_best_effort():
    session = AsyncMock()
    session.commit = AsyncMock()
    session.add = MagicMock()
    ok = await persist_andon_alert(
        session,
        tenant_id=TENANT,
        alert={
            "id": "AND-abc12345",
            "color": "red",
            "work_centre": "WC-WND",
            "reported_by": "Mohamed",
            "message": "Breakdown",
            "status": "active",
            "triggered_at": "2026-07-18T00:00:00+00:00",
        },
    )
    assert ok is True
    session.add.assert_called_once()
    session.commit.assert_awaited()


@pytest.mark.asyncio
async def test_persist_andon_invalid_tenant():
    session = AsyncMock()
    ok = await persist_andon_alert(session, tenant_id="not-a-uuid", alert={"id": "x", "color": "white"})
    assert ok is False


@pytest.mark.asyncio
async def test_save_mps_mrp_runs():
    session = AsyncMock()
    session.commit = AsyncMock()
    session.add = MagicMock()
    mps = await save_mps_run(session, tenant_id=TENANT, product_id="FG-DT100", payload={"rows": []})
    mrp = await save_mrp_run(session, tenant_id=TENANT, root_product_id="FG-DT100", payload={"lines": []})
    assert mps["persisted"] is True
    assert mrp["persisted"] is True


@pytest.mark.asyncio
async def test_stage_gate_api(client, auth_headers):
    reset_default_gate()
    resp = await client.get("/api/v1/planning-command/sop/stage-gate", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["current_stage"] == "demand_review"
    skip = await client.post(
        "/api/v1/planning-command/sop/stage-gate/skip",
        json={"note": "board request"},
        headers=auth_headers,
    )
    assert skip.status_code == 200
    assert skip.json()["data"]["current_stage"] == "management_review"


@pytest.mark.asyncio
async def test_andon_api_marks_persisted_flag(client, auth_headers):
    trig = await client.post(
        "/api/v1/planning-command/operations/andon",
        json={
            "color": "yellow",
            "work_centre": "WC-ASM",
            "reported_by": "Ahmed",
            "message": "Slow feed",
        },
        headers=auth_headers,
    )
    assert trig.status_code == 200
    body = trig.json()["data"]
    assert "persisted" in body
    assert body["status"] == "active"
