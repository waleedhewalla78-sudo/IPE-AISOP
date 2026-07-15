"""Supplier risk scoring and procurement compliance checks."""

from __future__ import annotations

DEFAULT_COMPLIANCE_RULES = [
    {"rule_id": "esg_min", "description": "ESG score must be at least 60", "field": "esg_score", "min_value": 60},
    {"rule_id": "risk_tier", "description": "Supplier risk tier must not be critical", "field": "risk_tier", "forbidden": ["critical"]},
    {"rule_id": "reliability_min", "description": "Reliability score must be at least 0.5", "field": "reliability_score", "min_value": 0.5},
]

DEFAULT_SPEND = [
    {"category": "raw_materials", "amount": 125000, "period": "2026-Q1"},
    {"category": "components", "amount": 89000, "period": "2026-Q1"},
    {"category": "logistics", "amount": 34000, "period": "2026-Q1"},
    {"category": "raw_materials", "amount": 118000, "period": "2026-Q2"},
    {"category": "components", "amount": 92000, "period": "2026-Q2"},
]


def check_supplier_compliance(supplier: dict, rules: list[dict] | None = None) -> list[dict]:
    rules = rules or DEFAULT_COMPLIANCE_RULES
    results = []
    for rule in rules:
        field = rule["field"]
        val = supplier.get(field)
        if val is None:
            results.append({"rule_id": rule["rule_id"], "result": "skip", "message": f"{field} not available"})
            continue
        ok = True
        message = rule.get("description", "")
        if rule.get("min_value") is not None:
            try:
                ok = float(val) >= float(rule["min_value"])
            except (TypeError, ValueError):
                ok = False
        if rule.get("forbidden") and str(val).lower() in [str(x).lower() for x in rule["forbidden"]]:
            ok = False
            message = f"{field}={val} is forbidden"
        results.append({"rule_id": rule["rule_id"], "result": "pass" if ok else "fail", "value": val, "message": message})
    return results


def aggregate_spend(rows: list[dict]) -> dict:
    by_category: dict[str, float] = {}
    by_period: dict[str, float] = {}
    total = 0.0
    for row in rows:
        amt = float(row.get("amount", 0))
        cat = row.get("category", "other")
        period = row.get("period", "unknown")
        by_category[cat] = by_category.get(cat, 0) + amt
        by_period[period] = by_period.get(period, 0) + amt
        total += amt
    return {"total": round(total, 2), "by_category": by_category, "by_period": by_period}


def score_supplier_risk(supplier: dict) -> dict:
    esg = float(supplier.get("esg_score") or 70)
    rel = float(supplier.get("reliability_score") or 0.7)
    tier = str(supplier.get("risk_tier") or "medium")
    tier_penalty = {"low": 0, "medium": 0.1, "high": 0.25, "critical": 0.5}.get(tier.lower(), 0.15)
    composite = round((esg / 100) * 0.4 + rel * 0.4 + (1 - tier_penalty) * 0.2, 4)
    return {"composite_score": composite, "risk_tier": tier, "esg_score": esg, "reliability_score": rel}


def recommend_purchase_orders(candidates: list[dict] | None = None) -> dict:
    """A9 weekly PO recommendation engine (in-memory / request-driven)."""
    candidates = candidates or [
        {
            "material_id": "RM-CW25",
            "material_name": "Copper Wire 2.5mm",
            "supplier": "Cairo Copper Industries",
            "qty": 800,
            "uom": "kg",
            "unit_price": 180,
            "lead_days": 8,
            "reliability": 0.68,
            "priority": 1,
            "alt_supplier": "National Wire Co.",
            "alt_unit_price": 192,
            "alt_reliability": 0.92,
        },
        {
            "material_id": "RM-SSL",
            "material_name": "Silicon Steel Lamination",
            "supplier": "Shanghai Silicon Steel Co.",
            "qty": 2000,
            "uom": "kg",
            "unit_price": 85,
            "lead_days": 21,
            "reliability": 0.91,
            "priority": 2,
            "alt_supplier": None,
            "alt_unit_price": None,
            "alt_reliability": None,
        },
    ]
    recommendations = []
    total = 0.0
    for c in candidates:
        line_total = float(c["qty"]) * float(c["unit_price"])
        total += line_total
        risk_note = None
        split = None
        if float(c.get("reliability") or 0) < 0.75 and c.get("alt_supplier"):
            risk_note = (
                f"{c['supplier']} reliability at {float(c['reliability'])*100:.0f}%. "
                f"Consider splitting with {c['alt_supplier']}."
            )
            q1 = int(float(c["qty"]) * 0.625)
            q2 = int(float(c["qty"]) - q1)
            premium = (float(c["alt_unit_price"]) - float(c["unit_price"])) * q2
            split = {
                "primary_qty": q1,
                "alt_qty": q2,
                "premium_cost": round(premium, 2),
            }
        recommendations.append(
            {
                "material_id": c["material_id"],
                "material_name": c["material_name"],
                "supplier": c["supplier"],
                "qty": c["qty"],
                "uom": c.get("uom", "kg"),
                "unit_price": c["unit_price"],
                "line_total": round(line_total, 2),
                "lead_days": c.get("lead_days"),
                "reliability": c.get("reliability"),
                "priority": c.get("priority", 2),
                "risk_note": risk_note,
                "split_recommendation": split,
                "actions": ["create_po", "create_po_split", "defer"] if split else ["create_po", "defer", "modify_qty"],
            }
        )
    deposit = round(total * 0.30, 2)
    return {
        "agent_id": "A9",
        "recommendations": recommendations,
        "summary": {
            "total_po_value": round(total, 2),
            "cash_requirement_deposit": deposit,
            "remaining_on_delivery": round(total - deposit, 2),
        },
    }
