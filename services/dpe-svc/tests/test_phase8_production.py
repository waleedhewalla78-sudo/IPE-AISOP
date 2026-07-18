"""Phase 8 Wave 1 — write-back dry-run, role gates, A18-A20 stubs, AI status."""

from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from app.core.phase8.write_back import (
    approve_write_back,
    propose_write_back,
    reset_write_back_store,
)
from app.core.phase8.agents import (
    a18_multi_site_split,
    a19_learning_retrain_stub,
    a20_exception_monitor_stub,
)
from app.main import app
from ipe_shared.auth.jwt import create_access_token
from ipe_shared.feature_flags.flags import get_feature_flags
from ipe_shared.roles import AgentRoleContext

TENANT = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"


@pytest.fixture(autouse=True)
def _clean_store():
    reset_write_back_store()
    flags = get_feature_flags()
    flags.set_enabled("ipe.odoo.live_writeback", False)
    yield
    reset_write_back_store()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_headers():
    token = create_access_token(user_id=UUID(TENANT), tenant_id=UUID(TENANT), role="manager")
    return {"Authorization": f"Bearer {token}", "X-Tenant-ID": TENANT}


def test_write_back_dry_run_never_live():
    entry = propose_write_back(
        tenant_id=TENANT,
        entity_type="mrp.production",
        entity_id="MO-1",
        field_name="date_planned_start",
        old_value="2026-07-20",
        new_value="2026-07-23",
        dry_run=True,
        financial_impact=500,
        user_role="supervisor",
    )
    assert entry["dry_run"] is True
    assert entry["is_live"] is False
    assert entry["status"] == "dry_run"
    assert entry["preview"]["executed"] is False
    assert "PH1-02" in entry["ph1_02_blocker"]


def test_write_back_approve_queues_without_live_flag():
    entry = propose_write_back(
        tenant_id=TENANT,
        entity_type="mrp.production",
        entity_id="MO-2",
        new_value="2026-08-01",
        dry_run=False,
        financial_impact=2000,
        user_role="manager",
    )
    result = approve_write_back(entry["id"], approved_by="mgr", user_role="manager", execute=True)
    assert result["is_live"] is False
    assert result["status"] == "queued"
    assert "live_writeback" in result["message"] or "PH1-02" in result.get("message", "")


def test_employee_cannot_approve_write_back():
    entry = propose_write_back(
        tenant_id=TENANT,
        entity_type="purchase.order",
        entity_id="PO-1",
        new_value="confirmed",
        dry_run=False,
        financial_impact=100,
        user_role="employee",
    )
    result = approve_write_back(entry["id"], approved_by="emp", user_role="employee", execute=True)
    assert result.get("error_message") == "insufficient_authority" or result["status"] == "pending_approval"


def test_a18_a19_a20_stubs():
    split = a18_multi_site_split(1000, {"A": 600, "B": 400})
    assert split["agent_id"] == "A18"
    assert split["status"] == "scaffold"
    assert abs(split["allocation"]["A"] + split["allocation"]["B"] - 1000) < 0.01

    learn = a19_learning_retrain_stub()
    assert learn["retrain_queued"] is False
    assert "8B" in learn["wave"]

    mon = a20_exception_monitor_stub(3)
    assert mon["open_exceptions"] == 3


def test_ai_status_endpoint(client, auth_headers):
    resp = client.get("/api/v1/phase8/ai-status", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    data = body.get("data") or body
    assert "ollama_available" in data
    assert "show_amber_banner" in data
    assert "banner_message_en" in data


def test_role_check_endpoint(client, auth_headers):
    resp = client.post(
        "/api/v1/phase8/role-check",
        headers=auth_headers,
        json={"user_role": "employee", "action": "approve_resolution", "financial_impact": 500},
    )
    assert resp.status_code == 200
    data = resp.json().get("data") or resp.json()
    assert data["allowed"] is False


def test_write_back_api_dry_run(client, auth_headers):
    resp = client.post(
        "/api/v1/phase8/write-back",
        headers=auth_headers,
        json={
            "entity_id": "MO-99",
            "new_value": "2026-07-25",
            "dry_run": True,
            "financial_impact": 1500,
            "user_role": "supervisor",
        },
    )
    assert resp.status_code == 200
    data = resp.json().get("data") or resp.json()
    assert data["dry_run"] is True
    assert data["is_live"] is False


def test_export_risk_queue_csv(client, auth_headers):
    resp = client.get("/api/v1/phase8/export/risk-queue.csv", headers=auth_headers)
    assert resp.status_code == 200
    assert "mo_id" in resp.text
    assert "text/csv" in resp.headers.get("content-type", "")


def test_thresholds_documented():
    assert AgentRoleContext.ROLE_CONFIGS["employee"]["max_financial_impact"] == 1000
    assert AgentRoleContext.ROLE_CONFIGS["supervisor"]["max_financial_impact"] == 10000
    assert AgentRoleContext.ROLE_CONFIGS["manager"]["max_financial_impact"] == 50000
