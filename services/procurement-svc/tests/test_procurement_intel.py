from app.core.procurement_intel import aggregate_spend, check_supplier_compliance, score_supplier_risk


def test_compliance_pass():
    supplier = {"esg_score": 75, "risk_tier": "low", "reliability_score": 0.85}
    results = check_supplier_compliance(supplier)
    assert all(r["result"] in ("pass", "skip") for r in results)


def test_compliance_fail_esg():
    supplier = {"esg_score": 40, "risk_tier": "low", "reliability_score": 0.85}
    results = check_supplier_compliance(supplier)
    assert any(r["rule_id"] == "esg_min" and r["result"] == "fail" for r in results)


def test_aggregate_spend():
    rows = [{"category": "raw_materials", "amount": 100, "period": "2026-Q1"}]
    summary = aggregate_spend(rows)
    assert summary["total"] == 100
    assert summary["by_category"]["raw_materials"] == 100


def test_score_supplier_risk():
    score = score_supplier_risk({"esg_score": 80, "reliability_score": 0.9, "risk_tier": "low"})
    assert score["composite_score"] > 0.5
