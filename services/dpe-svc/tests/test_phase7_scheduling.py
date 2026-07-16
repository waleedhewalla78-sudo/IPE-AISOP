"""Phase 7 §4 — Production Deep core tests (scheduling / labour / make-or-buy)."""

from app.core.phase7 import (
    analyze_make_or_buy,
    optimize_setup_sequence,
    plan_campaign,
    plan_labour,
    schedule_multi_resource,
)


def test_setup_sequence_optimisation_reduces_setup():
    data = optimize_setup_sequence(jobs=["DT100", "PT500", "DT100", "DT250"])
    assert data["optimised_setup_min"] <= data["before_setup_min"]
    assert data["savings_min"] == data["before_setup_min"] - data["optimised_setup_min"]
    # Grouping identical products removes intra-family setup.
    assert data["optimised_setup_min"] <= 60


def test_multi_resource_blocks_on_unavailable_material():
    data = schedule_multi_resource()
    assert data["schedulable"] is False
    assert data["binding_constraint"] == "Copper wire batch #089"
    assert data["escalation"]["to_agent"] == "A10"


def test_multi_resource_schedules_when_all_available():
    resources = [
        {"name": "Machine", "type": "machine", "available": True},
        {"name": "Operator", "type": "labour", "available": True},
    ]
    data = schedule_multi_resource(resources=resources)
    assert data["schedulable"] is True
    assert data["schedule"] is not None


def test_campaign_reduces_setups_and_reports_net_benefit():
    data = plan_campaign()
    assert data["campaign_setups"] == 3
    assert data["setup_savings_min"] > 0
    assert data["economics"]["net_benefit_usd"] != 0


def test_labour_flags_single_point_of_failure():
    data = plan_labour(critical_skill="Winding", critical_cert="PT500")
    # Only Mohamed holds Winding + PT500 in the default matrix → SPOF.
    assert data["spof_count"] == 1
    spof = data["single_point_of_failure"][0]
    assert spof["only_operator"] == "Mohamed"
    assert spof["cross_train_candidate"] is not None


def test_make_or_buy_dynamic_rule():
    below = analyze_make_or_buy(current_utilisation_pct=84, bottleneck_threshold_pct=90)
    assert below["decision"] == "make"
    above = analyze_make_or_buy(current_utilisation_pct=95, bottleneck_threshold_pct=90)
    assert above["decision"] == "buy"
    assert above["at_bottleneck"] is True
