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
