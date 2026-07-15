"""A8 Customer Intelligence — health scoring and delay notifications."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class CustomerHealthScore:
    customer_id: str
    customer_name: str
    overall: float
    trend: str
    risk: str
    components: dict[str, float]
    revenue_at_risk: float
    expansion_opportunity: str
    recommended_action: str
    details: dict[str, Any] = field(default_factory=dict)


def _clamp(v: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, v))


def score_customer_health(
    *,
    customer_id: str,
    customer_name: str,
    order_frequency_score: float = 80.0,
    payment_reliability_pct: float = 90.0,
    order_growth_yoy_pct: float = 0.0,
    complaint_count_12m: int = 0,
    delivery_otd_pct: float = 90.0,
    sla_otd_pct: float = 95.0,
    annual_revenue: float = 0.0,
) -> CustomerHealthScore:
    """Composite customer health (0–100) with action text."""
    growth_score = _clamp(70 + order_growth_yoy_pct)
    complaint_score = _clamp(100 - complaint_count_12m * 8)
    components = {
        "order_frequency": _clamp(order_frequency_score),
        "payment_reliability": _clamp(payment_reliability_pct),
        "order_growth": growth_score,
        "complaint_frequency": complaint_score,
        "delivery_satisfaction": _clamp(delivery_otd_pct),
    }
    weights = {
        "order_frequency": 0.15,
        "payment_reliability": 0.25,
        "order_growth": 0.15,
        "complaint_frequency": 0.20,
        "delivery_satisfaction": 0.25,
    }
    overall = round(sum(components[k] * weights[k] for k in components), 1)

    if overall >= 80:
        risk, trend = "low", "stable" if order_growth_yoy_pct >= 0 else "softening"
    elif overall >= 60:
        risk, trend = "medium", "watch"
    else:
        risk, trend = "high", "declining"

    otd_gap = sla_otd_pct - delivery_otd_pct
    revenue_at_risk = round(annual_revenue * 0.15, 2) if risk == "high" else (
        round(annual_revenue * 0.05, 2) if otd_gap > 5 else 0.0
    )
    expansion = "high" if order_growth_yoy_pct >= 10 and risk == "low" else (
        "medium" if risk != "high" else "low"
    )

    if otd_gap > 5:
        action = (
            f"{customer_name} OTD {delivery_otd_pct:.0f}% is below SLA {sla_otd_pct:.0f}%. "
            "Prioritise their MOs on constrained work centres."
        )
    elif risk == "high":
        action = f"{customer_name} health is declining — schedule account review this week."
    else:
        action = f"{customer_name} is healthy. Maintain service level; watch expansion signals."

    return CustomerHealthScore(
        customer_id=customer_id,
        customer_name=customer_name,
        overall=overall,
        trend=trend,
        risk=risk,
        components=components,
        revenue_at_risk=revenue_at_risk,
        expansion_opportunity=expansion,
        recommended_action=action,
        details={"sla_otd_pct": sla_otd_pct, "otd_gap": round(otd_gap, 1)},
    )


def draft_delay_notification(
    *,
    customer_name: str,
    order_number: str,
    product_desc: str,
    original_date: str,
    revised_date: str,
    reason: str,
    contact_name: str = "Planner",
    contact_email: str = "planner@example.com",
) -> dict[str, Any]:
    """Draft internal + customer-facing delay notification (no send)."""
    internal = (
        f"{customer_name} order {order_number} predicted late. "
        f"Call them before they call you. Revised: {revised_date} (was {original_date})."
    )
    customer = (
        f"Dear {customer_name},\n"
        f"Order {order_number} ({product_desc}) has an updated delivery estimate: "
        f"{revised_date} (originally {original_date}).\n"
        f"Reason: {reason}.\n"
        f"We are working to improve this timeline and will update you shortly.\n"
        f"Your dedicated contact: {contact_name} ({contact_email})"
    )
    return {
        "channel": "draft_only",
        "internal_alert": internal,
        "customer_notification": customer,
        "follow_up_required": True,
    }


class CustomerIntelligence:
    """A8 facade used by phase4 API / orchestrator dry-run."""

    def health(self, **kwargs: Any) -> dict[str, Any]:
        score = score_customer_health(**kwargs)
        return {
            "agent_id": "A8",
            "customer_id": score.customer_id,
            "customer_name": score.customer_name,
            "overall_health": score.overall,
            "trend": score.trend,
            "risk": score.risk,
            "components": score.components,
            "revenue_at_risk": score.revenue_at_risk,
            "expansion_opportunity": score.expansion_opportunity,
            "recommended_action": score.recommended_action,
            "details": score.details,
        }

    def delay_notice(self, **kwargs: Any) -> dict[str, Any]:
        return {"agent_id": "A8", **draft_delay_notification(**kwargs)}
