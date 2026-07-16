"""A13 Commercial Intelligence — SD-equivalent.

Pricing optimization, deal profitability analysis, and contract compliance
monitoring. Pure-logic core (no live ERP); reuses margin conventions from the
Phase 4 finance intelligence agent (A11).

Odoo Sales/Accounting reads are OUT OF SCOPE here — PH1-02 (live Odoo) is an
OPEN commercial blocker. Callers pass explicit numbers; a scaffolded
``OdooAccountingConnector`` (see ``odoo_accounting.py``) supplies mock figures
when no live feed is wired.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# Tier-based standard discount (%) — configurable per tenant in a real deploy.
TIER_DISCOUNT_PCT: dict[str, float] = {"A": 5.0, "B": 3.0, "C": 1.0}
# Competitive pressure → extra discount headroom the agent may recommend.
COMPETITIVE_DISCOUNT_PCT: dict[str, float] = {"low": 0.0, "medium": 3.0, "high": 5.0}


@dataclass
class PricingRecommendation:
    product_id: str
    customer_id: str
    customer_tier: str
    list_price: float
    recommended_price: float
    total_discount_pct: float
    margin_pct: float
    margin_floor_pct: float
    within_floor: bool
    within_discount_authority: bool
    requires_approval: bool
    alternative_price: float
    alternative_margin_pct: float
    rationale: list[str] = field(default_factory=list)


def optimize_price(
    *,
    product_id: str = "DT250",
    customer_id: str = "CUST-SEC",
    customer_tier: str = "A",
    list_price: float = 85_000.0,
    unit_cost: float = 64_400.0,
    quantity: int = 10,
    volume_discount_threshold: int = 5,
    volume_discount_pct: float = 3.0,
    competitive_pressure: str = "medium",
    margin_floor_pct: float = 20.0,
    planner_discount_authority_pct: float = 10.0,
    last_order_price: float | None = None,
) -> dict[str, Any]:
    """Recommend a price that protects margin while staying competitive.

    Returns a dict payload (API-friendly) with a primary recommendation and a
    higher-margin alternative, plus a discount-authority / approval flag.
    """
    tier = customer_tier.upper()
    tier_disc = TIER_DISCOUNT_PCT.get(tier, 0.0)
    vol_disc = volume_discount_pct if quantity >= volume_discount_threshold else 0.0
    comp_disc = COMPETITIVE_DISCOUNT_PCT.get(competitive_pressure.lower(), 0.0)

    total_disc = round(tier_disc + vol_disc + comp_disc, 2)
    recommended = round(list_price * (1 - total_disc / 100), 2)

    def _margin_pct(price: float) -> float:
        return round(((price - unit_cost) / price) * 100, 1) if price else 0.0

    rec_margin = _margin_pct(recommended)

    # If the recommended price breaches the floor, pull the discount back so
    # the price lands exactly on the floor margin.
    within_floor = rec_margin >= margin_floor_pct
    if not within_floor:
        floor_price = round(unit_cost / (1 - margin_floor_pct / 100), 2)
        recommended = floor_price
        total_disc = round((1 - recommended / list_price) * 100, 2)
        rec_margin = _margin_pct(recommended)
        within_floor = True

    # Alternative: a lighter discount (tier + volume only, no competitive give).
    alt_disc = round(tier_disc + vol_disc, 2)
    alt_price = round(list_price * (1 - alt_disc / 100), 2)
    alt_margin = _margin_pct(alt_price)

    within_authority = total_disc <= planner_discount_authority_pct
    requires_approval = (not within_authority) or (rec_margin < margin_floor_pct)

    rationale = [
        f"Tier {tier} standard discount {tier_disc}%",
        f"Volume discount {vol_disc}% ({quantity} units, threshold {volume_discount_threshold})",
        f"Competitive pressure '{competitive_pressure}' headroom {comp_disc}%",
        f"Recommended margin {rec_margin}% vs floor {margin_floor_pct}%",
    ]
    if last_order_price is not None:
        delta_pct = round((recommended - last_order_price) / last_order_price * 100, 1)
        rationale.append(f"vs last order {last_order_price:,.0f}: {delta_pct:+.1f}% change")
    if requires_approval:
        rationale.append(
            "Discount exceeds planner authority or margin below floor → approval required"
        )
    else:
        rationale.append("Within planner discount authority — no approval needed")

    rec = PricingRecommendation(
        product_id=product_id,
        customer_id=customer_id,
        customer_tier=tier,
        list_price=list_price,
        recommended_price=recommended,
        total_discount_pct=total_disc,
        margin_pct=rec_margin,
        margin_floor_pct=margin_floor_pct,
        within_floor=within_floor,
        within_discount_authority=within_authority,
        requires_approval=requires_approval,
        alternative_price=alt_price,
        alternative_margin_pct=alt_margin,
        rationale=rationale,
    )
    return {
        "agent_id": "A13",
        "capability": "pricing_optimization",
        "product_id": rec.product_id,
        "customer_id": rec.customer_id,
        "customer_tier": rec.customer_tier,
        "quantity": quantity,
        "list_price": rec.list_price,
        "recommended_price": rec.recommended_price,
        "recommended_revenue": round(rec.recommended_price * quantity, 2),
        "total_discount_pct": rec.total_discount_pct,
        "margin_pct": rec.margin_pct,
        "margin_floor_pct": rec.margin_floor_pct,
        "within_floor": rec.within_floor,
        "within_discount_authority": rec.within_discount_authority,
        "requires_approval": rec.requires_approval,
        "alternative": {
            "price": rec.alternative_price,
            "margin_pct": rec.alternative_margin_pct,
            "revenue": round(rec.alternative_price * quantity, 2),
        },
        "rationale": rec.rationale,
    }


def analyze_deal_profitability(
    *,
    order_id: str = "SO-2026-0289",
    revenue: float = 782_000.0,
    material_cost: float = 498_000.0,
    labour_cost: float = 62_000.0,
    overhead: float = 41_000.0,
    logistics_cost: float = 18_000.0,
    sales_cost: float = 15_000.0,
    target_margin_pct: float = 25.0,
    monthly_revenue_target: float = 2_100_000.0,
    monthly_revenue_so_far: float = 1_038_000.0,
    monthly_margin_target: float = 525_000.0,
    monthly_margin_so_far: float = 296_000.0,
    strategic_customer: bool = True,
) -> dict[str, Any]:
    """Full cost-stack deal P&L with target-gap and monthly contribution."""
    total_cost = material_cost + labour_cost + overhead + logistics_cost + sales_cost
    gross_profit = round(revenue - total_cost, 2)
    gross_pct = round((gross_profit / revenue) * 100, 1) if revenue else 0.0
    gap_pct = round(gross_pct - target_margin_pct, 1)

    rev_after = monthly_revenue_so_far + revenue
    margin_after = monthly_margin_so_far + gross_profit
    rev_attain = (
        round(rev_after / monthly_revenue_target * 100, 1) if monthly_revenue_target else 0.0
    )
    margin_attain = (
        round(margin_after / monthly_margin_target * 100, 1) if monthly_margin_target else 0.0
    )

    if gross_pct >= target_margin_pct:
        recommendation = "accept"
    elif strategic_customer:
        recommendation = "accept_flag_pricing_review"
    else:
        recommendation = "review"

    return {
        "agent_id": "A13",
        "capability": "deal_profitability",
        "order_id": order_id,
        "revenue": revenue,
        "cost_stack": {
            "material": material_cost,
            "labour": labour_cost,
            "overhead": overhead,
            "logistics": logistics_cost,
            "sales": sales_cost,
            "total": round(total_cost, 2),
        },
        "gross_profit": gross_profit,
        "gross_margin_pct": gross_pct,
        "target_margin_pct": target_margin_pct,
        "gap_pct": gap_pct,
        "monthly_contribution": {
            "revenue_after": round(rev_after, 2),
            "revenue_attainment_pct": rev_attain,
            "margin_after": round(margin_after, 2),
            "margin_attainment_pct": margin_attain,
        },
        "recommendation": recommendation,
    }


def check_contract_compliance(
    *,
    contract_id: str = "SEC-FRAMEWORK-2026",
    customer_name: str = "Saudi Electricity",
    annual_volume_commitment: int = 40,
    ytd_delivered: int = 28,
    agreed_price: float = 79_500.0,
    price_tolerance_pct: float = 3.0,
    current_quote_price: float = 78_200.0,
    delivery_sla_pct: float = 95.0,
    ytd_otd_pct: float = 88.0,
    quality_sla_defect_pct: float = 2.0,
    ytd_defect_pct: float = 1.2,
    payment_terms_compliance_pct: float = 95.0,
    penalty_clause_value: float = 50_000.0,
) -> dict[str, Any]:
    """Monitor framework-agreement compliance; emit SLA-breach alerts."""
    checks: list[dict[str, Any]] = []
    alerts: list[str] = []

    # Volume commitment pacing (proportional expectation not enforced — informational).
    volume_on_track = ytd_delivered <= annual_volume_commitment
    checks.append(
        {
            "dimension": "volume_commitment",
            "target": annual_volume_commitment,
            "actual": ytd_delivered,
            "status": "on_track" if volume_on_track else "over",
        }
    )

    price_low = agreed_price * (1 - price_tolerance_pct / 100)
    price_high = agreed_price * (1 + price_tolerance_pct / 100)
    price_ok = price_low <= current_quote_price <= price_high
    checks.append(
        {
            "dimension": "price_agreement",
            "range": [round(price_low, 2), round(price_high, 2)],
            "actual": current_quote_price,
            "status": "within_range" if price_ok else "out_of_range",
        }
    )
    if not price_ok:
        alerts.append(
            f"Quote {current_quote_price:,.0f} outside agreed range "
            f"[{price_low:,.0f}, {price_high:,.0f}] for {customer_name}."
        )

    otd_ok = ytd_otd_pct >= delivery_sla_pct
    checks.append(
        {
            "dimension": "delivery_sla",
            "target": delivery_sla_pct,
            "actual": ytd_otd_pct,
            "status": "met" if otd_ok else "breached",
        }
    )
    if not otd_ok:
        alerts.append(
            f"OTD to {customer_name} below contract SLA ({ytd_otd_pct}% vs {delivery_sla_pct}%). "
            f"Penalty clause (${penalty_clause_value:,.0f}) risk activates at year-end. "
            f"RECOMMENDATION: prioritize {customer_name} orders in A3 scheduling."
        )

    quality_ok = ytd_defect_pct <= quality_sla_defect_pct
    checks.append(
        {
            "dimension": "quality_sla",
            "target_max": quality_sla_defect_pct,
            "actual": ytd_defect_pct,
            "status": "met" if quality_ok else "breached",
        }
    )
    if not quality_ok:
        alerts.append(
            f"Defect rate {ytd_defect_pct}% exceeds SLA "
            f"{quality_sla_defect_pct}% for {customer_name}."
        )

    payment_ok = payment_terms_compliance_pct >= 90.0
    checks.append(
        {
            "dimension": "payment_terms",
            "target": 90.0,
            "actual": payment_terms_compliance_pct,
            "status": "met" if payment_ok else "at_risk",
        }
    )

    breaches = [c for c in checks if c["status"] in ("breached", "out_of_range")]
    overall = "compliant" if not breaches else "at_risk"

    return {
        "agent_id": "A13",
        "capability": "contract_compliance",
        "contract_id": contract_id,
        "customer_name": customer_name,
        "overall_status": overall,
        "checks": checks,
        "alerts": alerts,
        "penalty_exposure": penalty_clause_value if not otd_ok else 0.0,
    }


class CommercialIntelligence:
    """A13 facade — mirrors the FinanceIntelligence/CustomerIntelligence style."""

    agent_id = "A13"
    name = "Commercial Intelligence"

    def price(self, **kwargs: Any) -> dict[str, Any]:
        return optimize_price(**kwargs)

    def deal(self, **kwargs: Any) -> dict[str, Any]:
        return analyze_deal_profitability(**kwargs)

    def contract(self, **kwargs: Any) -> dict[str, Any]:
        return check_contract_compliance(**kwargs)
