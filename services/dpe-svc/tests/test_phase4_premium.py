"""Phase 4 Premium unit tests — A8/A11/autonomy/pulse."""

import pytest

from app.core.phase4 import (
    AutonomousRuleEngine,
    CustomerIntelligence,
    FinanceIntelligence,
    build_intelligence_pulse,
)


def test_customer_health_otd_gap_action():
    a8 = CustomerIntelligence()
    data = a8.health(
        customer_id="C1",
        customer_name="Saudi Electricity Company",
        delivery_otd_pct=88,
        sla_otd_pct=95,
        order_growth_yoy_pct=12,
        payment_reliability_pct=95,
        complaint_count_12m=1,
    )
    assert data["agent_id"] == "A8"
    assert data["overall_health"] >= 70
    assert "SLA" in data["recommended_action"] or "OTD" in data["recommended_action"]


def test_delay_notice_draft():
    a8 = CustomerIntelligence()
    n = a8.delay_notice(
        customer_name="SEC",
        order_number="SO-1",
        product_desc="DT250",
        original_date="2026-08-10",
        revised_date="2026-08-13",
        reason="Capacity",
    )
    assert "draft_only" == n["channel"]
    assert "SO-1" in n["customer_notification"]


def test_mo_margin_alert_when_below_target():
    a11 = FinanceIntelligence()
    m = a11.mo_margin(
        mo_id="MO-ST-004",
        revenue=255_000,
        material_cost=174_000,
        labour_cost=12_600,
        overhead=8_400,
        standard_material=169_800,
        target_margin_pct=25,
    )
    assert m["gross_margin_pct"] < 25
    assert m["alert"]


def test_decision_pnl_roi():
    a11 = FinanceIntelligence()
    d = a11.decision_pnl(
        decision="Approve overtime",
        direct_cost=1800,
        revenue_protected=85_000,
        penalty_avoided=6000,
    )
    assert d["recommendation"] == "approve"
    assert d["roi"] and d["roi"] > 1


def test_cash_flow_threshold_alert():
    a11 = FinanceIntelligence()
    cf = a11.cash_flow(
        [
            {"week": "W29", "inflows": 180_000, "outflows": 94_200},
            {"week": "W30", "inflows": 85_000, "outflows": 219_800},
        ],
        opening_balance=256_200,
        threshold=250_000,
    )
    assert any(w["below_threshold"] for w in cf["weeks"])
    assert cf["alerts"]


def test_intelligence_pulse_six_modules():
    pulse = build_intelligence_pulse(tenant_id="t1", planner_name="Ahmed")
    assert len(pulse["modules"]) == 6
    assert {m["module_id"] for m in pulse["modules"]} == {"M1", "M2", "M3", "M4", "M5", "M6"}
    assert "attention" in pulse["pulse"]["brief"].lower() or "Ahmed" in pulse["pulse"]["brief"]


def test_autonomous_blocks_a_customer():
    engine = AutonomousRuleEngine()
    result = engine.evaluate_overnight(
        {
            "resolutions": [
                {
                    "mo_id": "MO-1",
                    "customer_priority": "A",
                    "delay_days": 1,
                    "cost": 0,
                    "feasibility_score": 60,
                }
            ],
            "reorder_candidates": [],
            "batch_candidates": [],
            "quality_risks": [],
        }
    )
    assert result["actions"][0]["status"] == "blocked"


def test_autonomous_applies_b_customer_and_quality():
    engine = AutonomousRuleEngine()
    result = engine.evaluate_overnight(
        {
            "resolutions": [
                {
                    "mo_id": "MO-ST-009",
                    "customer_priority": "B",
                    "delay_days": 1,
                    "cost": 0,
                    "feasibility_score": 65,
                }
            ],
            "reorder_candidates": [
                {
                    "material_id": "RM-SSL",
                    "po_value": 40_000,
                    "supplier_reliability": 0.91,
                    "below_reorder": True,
                }
            ],
            "batch_candidates": [
                {
                    "product_family": "DT100",
                    "changeover_savings_min": 45,
                    "same_priority_level": True,
                    "no_delivery_violation": True,
                }
            ],
            "quality_risks": [
                {"mo_id": "MO-ST-008", "defect_probability": 0.23, "customer_priority": "A"}
            ],
        }
    )
    statuses = {a["rule_id"]: a["status"] for a in result["actions"]}
    assert statuses["RULE1_AUTO_APPROVE"] == "applied"
    assert statuses["RULE2_AUTO_PO"] == "applied"
    assert statuses["RULE3_AUTO_BATCH"] == "applied"
    assert statuses["RULE4_QUALITY_ESCALATE"] == "applied"
    assert result["actions_taken"] == 4


@pytest.mark.asyncio
async def test_orchestrator_includes_phase4_agents_when_data_changed():
    from app.core.agent_orchestrator import AgentOrchestrator

    orch = AgentOrchestrator(dry_run=True)
    result = await orch.run_chain(
        "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
        "phase4",
        ["demand", "inventory", "production", "supply", "customer", "finance", "master"],
    )
    details = result["details"]
    assert "A8" in details
    assert "A11" in details
