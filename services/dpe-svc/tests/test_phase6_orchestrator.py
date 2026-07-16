"""Phase 6C — A17 Cross-Functional Orchestrator unit tests.

Includes the headline cross-functional ATP/CTP scenario (A17 coordinating
A1/A3/A11/A13).
"""

from app.core.phase6 import AgentRecommendation, CrossFunctionalOrchestrator

A17 = CrossFunctionalOrchestrator()


def test_resolution_hierarchy_customer_sla_beats_cost():
    # A8 defends customer SLA; A3 wants cost optimization (delay).
    recs = [
        AgentRecommendation(
            agent_id="A8", action="hold_delivery_date", impacts={"customer_sla": 1.0}
        ),
        AgentRecommendation(agent_id="A3", action="delay_mo", impacts={"cost_optimization": 1.0}),
    ]
    result = A17.resolve_conflict(recs)
    assert result["winner"]["agent_id"] == "A8"
    assert result["mode"] == "autonomous"
    assert result["reversible"] is True


def test_resolution_escalates_when_approval_required():
    recs = [
        AgentRecommendation(
            agent_id="A13",
            action="accept_below_floor",
            impacts={"revenue_protection": 1.0},
            requires_human_approval=True,
            approval_role="commercial_director",
        ),
    ]
    result = A17.resolve_conflict(recs)
    assert result["mode"] == "escalation"
    assert result["escalate_to"] == "commercial_director"
    assert result["governance_level"] == 3


def test_policy_gate_blocks_on_quality():
    p = A17.enforce_policies({"defect_probability_pct": 25.0, "order_margin_pct": 30.0})
    assert p["gate"] == "block"
    q = next(x for x in p["policies"] if x["policy"] == "P6_quality_non_negotiable")
    assert q["status"] == "block"


def test_policy_gate_blocks_below_margin_floor():
    p = A17.enforce_policies(
        {"order_margin_pct": 8.0, "margin_floor_pct": 15.0, "strategic_customer": False}
    )
    assert p["gate"] == "block"


def test_policy_margin_floor_review_when_strategic_board_approved():
    p = A17.enforce_policies(
        {
            "order_margin_pct": 8.0,
            "margin_floor_pct": 15.0,
            "strategic_customer": True,
            "board_approved": True,
            "defect_probability_pct": 5.0,
        }
    )
    p4 = next(x for x in p["policies"] if x["policy"] == "P4_margin_floor")
    assert p4["status"] == "review"


def test_policy_cash_flow_and_single_source_flags():
    p = A17.enforce_policies(
        {
            "order_margin_pct": 30.0,
            "committed_po_value": 800_000,
            "cash_reserves": 1_000_000,
            "max_supplier_share_pct": 90.0,
            "defect_probability_pct": 5.0,
        }
    )
    p2 = next(x for x in p["policies"] if x["policy"] == "P2_cash_flow_protection")
    p3 = next(x for x in p["policies"] if x["policy"] == "P3_single_source_risk")
    assert p2["status"] == "review"  # 80% > 60% limit
    assert p3["status"] == "review"  # 90% > 80% limit
    assert p["gate"] == "review"


def test_policy_all_clear_allows():
    p = A17.enforce_policies(
        {
            "customer_tier": "A",
            "order_margin_pct": 24.0,
            "committed_po_value": 300_000,
            "cash_reserves": 1_240_000,
            "max_supplier_share_pct": 55.0,
            "margin_floor_pct": 15.0,
            "carbon_delta_pct": -6.0,
            "defect_probability_pct": 5.0,
        }
    )
    assert p["gate"] == "allow"


def test_cascade_event_coordinates_agents():
    c = A17.cascade_event({"type": "demand_change", "product_id": "FG-DT100", "delta_units": 38})
    assert c["coordinated_agents"][0] == "A1"
    assert "A11" in c["coordinated_agents"]
    assert len(c["chain"]) == 7
    assert c["resolution"] == "coordinated_plan_ready"


def test_orchestrate_atp_headline_accept():
    r = A17.orchestrate_atp(
        qty=50,
        inventory_available=12,
        capacity_available_hrs=200,
        material_lead_days=8,
    )
    assert r["coordinated_agents"] == ["A1", "A3", "A11", "A13", "A17"]
    assert r["decision"] in ("accept", "negotiate")
    assert r["commercial"]["margin_pct"] > 0
    assert r["finance"]["net_impact"] is not None
    assert r["policy_gate"] in ("allow", "review", "block")


def test_orchestrate_atp_rejects_on_quality_block():
    r = A17.orchestrate_atp(
        qty=50,
        inventory_available=12,
        capacity_available_hrs=200,
        defect_probability_pct=30.0,
    )
    assert r["policy_gate"] == "block"
    assert r["decision"] == "reject"
    assert r["governance_level"] == 4
