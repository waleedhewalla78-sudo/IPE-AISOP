"""Phase 6A — A13 Commercial Intelligence unit tests."""

from app.core.phase6 import (
    analyze_deal_profitability,
    check_contract_compliance,
    optimize_price,
)


def test_pricing_applies_tier_volume_and_competitive_discount():
    p = optimize_price(
        customer_tier="A",
        list_price=85_000,
        unit_cost=59_200,
        quantity=10,
        competitive_pressure="low",
        margin_floor_pct=20,
    )
    # Tier A 5% + volume 3% + competitive 0% = 8% discount; margin stays > floor.
    assert p["total_discount_pct"] == 8.0
    assert p["recommended_price"] == 85_000 * 0.92
    assert p["margin_pct"] > 20  # ~24.3% per doc example
    assert p["within_floor"] is True
    assert p["agent_id"] == "A13"


def test_pricing_respects_margin_floor():
    # Deep discount that would breach floor gets pulled back to the floor.
    p = optimize_price(
        customer_tier="A",
        list_price=100_000,
        unit_cost=85_000,
        quantity=10,
        competitive_pressure="high",
        margin_floor_pct=20,
    )
    assert p["within_floor"] is True
    assert p["margin_pct"] >= 20.0


def test_pricing_flags_approval_when_over_authority():
    p = optimize_price(
        customer_tier="A",
        list_price=100_000,
        unit_cost=50_000,
        quantity=10,
        competitive_pressure="high",
        margin_floor_pct=20,
        planner_discount_authority_pct=5.0,
    )
    # 5 + 3 + 5 = 13% > 5% authority.
    assert p["requires_approval"] is True
    assert p["within_discount_authority"] is False


def test_deal_profitability_gap_and_contribution():
    d = analyze_deal_profitability(
        revenue=782_000,
        material_cost=498_000,
        labour_cost=62_000,
        overhead=41_000,
        logistics_cost=18_000,
        sales_cost=15_000,
        target_margin_pct=25,
        strategic_customer=True,
    )
    assert d["cost_stack"]["total"] == 634_000
    assert d["gross_profit"] == 148_000
    assert d["gross_margin_pct"] == 18.9
    assert d["gap_pct"] < 0
    assert d["recommendation"] == "accept_flag_pricing_review"
    assert "revenue_attainment_pct" in d["monthly_contribution"]


def test_deal_accept_when_above_target():
    d = analyze_deal_profitability(
        revenue=1_000_000,
        material_cost=500_000,
        labour_cost=100_000,
        overhead=50_000,
        logistics_cost=20_000,
        sales_cost=10_000,
        target_margin_pct=25,
    )
    assert d["gross_margin_pct"] >= 25
    assert d["recommendation"] == "accept"


def test_contract_compliance_flags_otd_breach():
    c = check_contract_compliance(
        delivery_sla_pct=95,
        ytd_otd_pct=88,
        current_quote_price=78_200,
        agreed_price=79_500,
    )
    assert c["overall_status"] == "at_risk"
    assert c["penalty_exposure"] == 50_000
    assert any("OTD" in a for a in c["alerts"])
    otd = next(x for x in c["checks"] if x["dimension"] == "delivery_sla")
    assert otd["status"] == "breached"


def test_contract_compliance_price_within_range():
    c = check_contract_compliance(
        current_quote_price=78_200,
        agreed_price=79_500,
        price_tolerance_pct=3,
        ytd_otd_pct=96,
    )
    price = next(x for x in c["checks"] if x["dimension"] == "price_agreement")
    assert price["status"] == "within_range"
