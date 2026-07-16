"""Phase 6B — A15 Procurement Execution + A16 Shop Floor unit tests."""

from app.core.phase6 import (
    OdooAccountingConnector,
    build_work_instructions,
    confirm_receipt,
    production_progress,
    three_way_match,
    track_time,
)


def test_three_way_match_auto_approve_when_clean_and_under_ceiling():
    r = three_way_match(
        lines=[
            {
                "line_id": "L1",
                "material_id": "RM-CW25",
                "po_qty": 200,
                "received_qty": 200,
                "invoiced_qty": 200,
                "po_unit_price": 12.0,
                "invoice_unit_price": 12.0,
            }
        ],
        auto_approve_ceiling=50_000,
    )
    assert r["all_matched"] is True
    assert r["routing"] == "auto_approve"
    assert r["exceptions"] == []
    assert r["erp_writeback"]["live"] is False


def test_three_way_match_blocks_on_mismatch():
    r = three_way_match()  # default L2 has qty + price deviation
    assert r["all_matched"] is False
    assert r["routing"] == "block_and_investigate"
    assert len(r["exceptions"]) >= 1


def test_three_way_match_routes_for_approval_over_ceiling():
    r = three_way_match(
        lines=[
            {
                "line_id": "L1",
                "material_id": "RM-CW25",
                "po_qty": 5000,
                "received_qty": 5000,
                "invoiced_qty": 5000,
                "po_unit_price": 20.0,
                "invoice_unit_price": 20.0,
            }
        ],
        auto_approve_ceiling=50_000,
    )
    assert r["all_matched"] is True
    assert r["routing"] == "route_for_approval"


def test_confirm_receipt_partial_and_reject():
    partial = confirm_receipt(ordered_qty=200, received_qty=180)
    assert partial["status"] == "partial_receipt"
    assert partial["variance"] == -20
    rejected = confirm_receipt(inspection_passed=False)
    assert rejected["status"] == "rejected_inspection"


def test_work_instructions_ordered_and_totaled():
    w = build_work_instructions()
    seqs = [s["seq"] for s in w["steps"]]
    assert seqs == sorted(seqs)
    assert w["total_std_minutes"] == sum(s["std_minutes"] for s in w["steps"])


def test_time_track_flags_over_standard():
    t = track_time(std_minutes=180, actual_minutes=205)
    assert t["variance_minutes"] == 25
    assert t["alert"] is not None
    fast = track_time(std_minutes=180, actual_minutes=170)
    assert fast["alert"] is None
    assert fast["efficiency_pct"] > 100


def test_production_progress_aggregates_and_flags_deviation():
    p = production_progress()
    assert 0 <= p["overall_pct_complete"] <= 100
    assert p["status"] == "in_progress"
    assert any("behind schedule" in d for d in p["deviations"])
    assert p["iot_telemetry"]["live"] is False


def test_odoo_accounting_connector_is_mock():
    conn = OdooAccountingConnector()
    assert conn.is_live is False
    status = conn.status()
    assert status["mode"] == "mock"
    assert "PH1-02" in status["blocker"]
    aging = conn.ap_ar_aging("tenant-1")
    assert aging["live"] is False
    assert "accounts_receivable" in aging
