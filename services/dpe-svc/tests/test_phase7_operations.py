"""Phase 7 §5 — Operations Deep core tests (OEE / Gemba / Andon / KPI / SW)."""

from app.core.phase7 import (
    AndonBoard,
    build_gemba,
    build_kpi_tree,
    build_oee_programme,
    build_planning_calendar,
    build_standard_work,
)


def test_oee_programme_targets_and_payback():
    data = build_oee_programme()
    assert data["current_oee_pct"] < data["target_oee_pct"]
    assert data["improvement_pp"] > 0
    assert data["total_annual_saving_usd"] > 0
    assert data["payback_days"] >= 0
    assert len(data["plan"]) == 3


def test_gemba_flags_slow_and_marks_iot_stub():
    data = build_gemba(speed_threshold_pct=90.0)
    assert data["iot_live"] is False  # honest live-integration stub
    wnd = next(w for w in data["work_centres"] if w["wc"] == "WC-WND")
    assert wnd["speed_below_threshold"] is True
    assert any(o["wc"] == "WC-WND" for o in data["observations"])


def test_andon_trigger_resolve_and_board():
    board = AndonBoard()
    red = board.trigger(
        color="red", work_centre="WC-WND", reported_by="Mohamed", message="Breakdown"
    )
    assert red["response_minutes"] == 15
    assert red["escalate_after_minutes"] == 30
    assert "maintenance" in red["notify"]
    blue = board.trigger(
        color="blue", work_centre="WC-ASM", reported_by="Ahmed", message="Missing paper"
    )
    assert blue["status"] == "active"
    b = board.board()
    assert b["statistics"]["active"] == 2
    resolved = board.resolve(red["id"], "Motor replaced")
    assert resolved["status"] == "resolved"
    assert board.resolve("nonexistent", "x") is None
    b2 = board.board()
    assert b2["statistics"]["active"] == 1
    assert b2["statistics"]["resolved"] == 1


def test_kpi_tree_four_levels_and_attention():
    data = build_kpi_tree()
    assert "level_0_factory" in data
    assert "level_3_operators" in data
    # WC-WND OEE 71 < 75 threshold → flagged.
    assert "WC-WND" in data["attention_work_centres"]
    wnd = next(w for w in data["level_2_work_centres"] if w["wc"] == "WC-WND")
    assert wnd["operators"]


def test_standard_work_tracks_over_standard_steps():
    data = build_standard_work(actuals={4: 240})  # 240 vs 180 std = 133% > 120%
    step4 = next(s for s in data["steps"] if s["step"] == 4)
    assert step4["over_standard"] is True
    assert any(f["step"] == 4 for f in data["over_standard_steps"])
    assert data["total_standard_min"] > 0


def test_planning_calendar_all_and_filtered():
    full = build_planning_calendar()
    assert set(full["cadences"]) == {"daily", "weekly", "monthly", "quarterly", "annually"}
    assert full["total_activities"] > 0
    daily = build_planning_calendar(cadence="daily")
    assert daily["cadence"] == "daily"
    assert daily["count"] == len(daily["entries"])
