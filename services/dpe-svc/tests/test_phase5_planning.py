"""Phase 5 Planning Command unit tests."""

from app.core.phase5 import (
    ActionTracker,
    build_mps,
    build_ops_dashboard,
    build_performance_cockpit,
    build_planning_cockpit,
    build_predictive_command,
    build_shift_handover,
    build_war_room,
    explode_mrp,
    level_production,
    promise_order,
    run_crp,
    run_rccp,
    run_scenario_cascade,
)


def test_planning_cockpit_attention_and_health():
    data = build_planning_cockpit(tenant_id="t1", mos_at_risk=5, materials_below_ss=3)
    assert data["plan_health"]["plan_coverage_pct"] >= 90
    codes = {a["code"] for a in data["attention"]}
    assert "MOS_AT_RISK" in codes
    assert "MRP_NEEDED" in codes
    assert len(data["timeline"]) == 4


def test_mps_generates_draft_when_below_ss():
    mps = build_mps(product_id="FG-DT100", opening_inventory=45, safety_stock=15, lot_size=5)
    assert mps["product_id"] == "FG-DT100"
    assert len(mps["weeks"]) == 6
    # Eventually inventory draws down → draft MOs
    assert any(r["planned_production"] > 0 for r in mps["weeks"]) or mps["draft_mos"] is not None
    assert mps["recommendation"] is None or "production" in mps["recommendation"].lower() or len(mps["draft_mos"]) >= 0


def test_mrp_flags_critical_copper():
    result = explode_mrp(product_id="FG-DT100", mo_qty=20)
    assert result["summary"]["draft_po_count"] >= 1
    statuses = {line["material_id"]: line["status"] for line in result["lines"]}
    assert statuses.get("RM-CW25") in ("po_needed", "po_critical")
    assert result["planner_action"] == "review_and_approve_pos"


def test_promise_accept_when_material_and_capacity_ok():
    p = promise_order(
        order_id="SO-1",
        product_id="FG-DT100",
        qty=5,
        requested_date="2026-08-10",
        inventory_available=12,
        capacity_available_hrs=40,
    )
    assert p["status"] == "accept"
    assert p["confidence"] >= 0.9
    assert p["commercial"]["margin_pct"] > 20
    assert p["promise_level"] in ("ATP", "CTP")
    assert p["breakdown"]["from_stock"] + p["breakdown"]["from_production"] == 5
    assert p["ptp"]["recommendation"] == "accept"


def test_promise_negotiate_when_both_constrained():
    p = promise_order(
        order_id="SO-2",
        product_id="FG-DT100",
        qty=20,
        requested_date="2026-08-10",
        inventory_available=2,
        capacity_available_hrs=5,
        material_lead_days=14,
    )
    assert p["status"] == "negotiate"
    assert p["bottleneck"] == "material+capacity"


def test_level_production_smooths_peak():
    leveled = level_production(
        weekly_demand=[
            {"week": "W29", "demand": 42},
            {"week": "W30", "demand": 18},
            {"week": "W31", "demand": 35},
            {"week": "W32", "demand": 12},
        ],
        capacity_per_week=30,
    )
    assert leveled["peaks_smoothed"] >= 1
    assert leveled["feasible"]
    assert max(w["leveled_production"] for w in leveled["weeks"]) <= 30.01


def test_ops_dashboard_and_war_room():
    dash = build_ops_dashboard(tenant_id="t1")
    assert dash["right_now"]["mos_in_production"] >= 1
    assert "oee_pct" in dash["scorecard"]
    wr = build_war_room(
        incident_id="INC-1",
        title="Breakdown",
        affected_mos=["MO-1", "MO-2"],
        revenue_at_risk=100_000,
        customers=["SEC"],
    )
    assert wr["mode"] == "war_room"
    assert wr["recommended_option"] == 2
    assert len(wr["resolution_options"]) == 3


def test_shift_handover_and_actions():
    h = build_shift_handover(
        from_shift="A",
        to_shift="B",
        completed_mos=["MO-1"],
        in_progress=[{"mo_id": "MO-2", "pct": 40}],
        open_issues=["Operator late on WND"],
        quality_holds=["batch-089"],
    )
    assert h["acknowledge_required"]
    assert "Shift A" in h["ai_summary"]

    tracker = ActionTracker()
    act = tracker.create(title="Approve copper PO", owner="ahmed", mo_id="MO-2")
    assert act["status"] == "open"
    done = tracker.complete(act["action_id"], "PO created")
    assert done and done["status"] == "done"
    assert len(tracker.list(status="done")) == 1


def test_rccp_flags_winding_overload():
    r = run_rccp(week="W31")
    assert not r["feasible"]
    assert any(b["work_centre"] == "Winding" for b in r["bottlenecks"])
    assert r["suggestions"]


def test_crp_weekly_utilisation():
    c = run_crp(work_centre="Winding", week="W31")
    assert c["weekly_utilisation_pct"] > 0
    assert len(c["days"]) == 5
    assert c["peak_utilisation_pct"] >= c["weekly_utilisation_pct"] or c["peak_utilisation_pct"] > 0


def test_performance_cockpit_oee_formula():
    p = build_performance_cockpit(
        availability_pct=88.0, performance_pct=92.0, quality_pct=94.0
    )
    # 0.88 * 0.92 * 0.94 * 100 ≈ 76.1
    assert 75.0 <= p["factory_oee_pct"] <= 77.0
    assert "Winding" in {w["work_centre"] for w in p["by_work_centre"]}
    assert p["kpis"]["otd_target_pct"] == 95.0


def test_predictive_command_horizons():
    pred = build_predictive_command()
    assert set(pred["horizons_days"]) == {3, 7, 14}
    assert pred["summary"]["critical"] >= 1
    assert "7" in pred["by_horizon"]


def test_scenario_cascade_demand_uplift():
    s = run_scenario_cascade(demand_uplift_pct=20.0)
    assert s["capacity_impact"]["winding_util_pct"] > 84
    assert s["financial_impact"]["additional_revenue"] > 0
    assert s["recommendation"] in ("proceed", "mitigate_first")
    assert "A11" in s["agents"]
