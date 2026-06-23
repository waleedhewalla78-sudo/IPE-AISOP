import pytest

from app.api.v1.delay import VALID_CATEGORIES, DelayCategory
from app.core.rule_classifier import classify_by_rules


@pytest.mark.asyncio
async def test_health_endpoint(client):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["service"] == "del-svc"


@pytest.mark.asyncio
async def test_classify_no_tenant(client):
    response = await client.post("/api/v1/delay/classify", json={"source_text": "test"})
    assert response.status_code == 200
    assert response.json()["error"]["code"] == "NO_TENANT"


@pytest.mark.asyncio
async def test_chatter_no_tenant(client):
    from uuid import uuid4
    response = await client.post(
        "/api/v1/delay/chatter",
        json={"mo_id": str(uuid4()), "chatter_text": "test"},
    )
    assert response.status_code == 200
    assert response.json()["error"]["code"] == "NO_TENANT"


@pytest.mark.asyncio
async def test_pareto_no_tenant(client):
    response = await client.get("/api/v1/delay/pareto")
    assert response.status_code == 200
    assert response.json()["error"]["code"] == "NO_TENANT"


def test_delay_category_enum_values():
    expected = {
        "material_shortage", "capacity_overload", "labor_absence",
        "supplier_delay", "maintenance", "quality_issue",
        "process_variance", "other",
    }
    actual = {c.value for c in DelayCategory}
    assert actual == expected


def test_valid_categories_matches_enum():
    assert VALID_CATEGORIES == {c.value for c in DelayCategory}


def test_rule_classifier_material_shortage():
    result = classify_by_rules({"source_text": "out of stock for raw material, shortage detected"})
    assert result["cause_category"] == "material_shortage"
    assert result["confidence"] >= 0.4


def test_rule_classifier_capacity_overload():
    result = classify_by_rules({"source_text": "work center fully booked, no capacity available"})
    assert result["cause_category"] == "capacity_overload"
    assert result["confidence"] >= 0.5


def test_rule_classifier_labor_absence():
    result = classify_by_rules({"source_text": "operator absent today, no show, unavailable"})
    assert result["cause_category"] == "labor_absence"
    assert result["confidence"] >= 0.5


def test_rule_classifier_supplier_delay():
    result = classify_by_rules({"source_text": "supplier late, shipment delayed, order not arrived"})
    assert result["cause_category"] == "supplier_delay"
    assert result["confidence"] >= 0.5


def test_rule_classifier_maintenance():
    result = classify_by_rules({"source_text": "machine breakdown, equipment failure, downtime reported"})
    assert result["cause_category"] == "maintenance"
    assert result["confidence"] >= 0.5


def test_rule_classifier_quality_issue():
    result = classify_by_rules({"source_text": "defect found, rework required, failed inspection"})
    assert result["cause_category"] == "quality_issue"
    assert result["confidence"] >= 0.5


def test_rule_classifier_process_variance():
    result = classify_by_rules({"source_text": "cycle time took longer than expected"})
    assert result["cause_category"] == "process_variance"
    assert result["confidence"] > 0.5


def test_rule_classifier_other_fallback():
    result = classify_by_rules({"source_text": "something happened"})
    assert result["cause_category"] == "other"
    assert result["confidence"] <= 0.5


def test_rule_classifier_constrained_to_valid_categories():
    for _ in range(20):
        result = classify_by_rules({"source_text": f"test {DelayCategory.OTHER.value}"})
        assert result["cause_category"] in VALID_CATEGORIES
