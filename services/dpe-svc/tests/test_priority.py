from datetime import UTC, datetime, timedelta

from app.core.classifier import classify_demand_type
from app.core.priority import calculate_priority


def test_calculate_priority_returns_dict():
    result = calculate_priority({})
    assert isinstance(result, dict)
    assert "priority_score" in result
    assert "components" in result
    assert "priority_breakdown" in result


def test_calculate_priority_urgent():
    result = calculate_priority({
        "required_date": (datetime.now(UTC) + timedelta(days=1)).isoformat(),
        "customer_tier": 1,
        "penalty_cost": 50000,
        "margin_pct": 30,
        "quantity": 1000,
    })
    assert result["priority_score"] > 0.7


def test_calculate_priority_not_urgent():
    result = calculate_priority({
        "required_date": (datetime.now(UTC) + timedelta(days=60)).isoformat(),
        "customer_tier": 3,
        "penalty_cost": 0,
        "quantity": 10,
    })
    assert result["priority_score"] < 0.6


def test_calculate_priority_with_breakdown():
    result = calculate_priority({
        "required_date": (datetime.now(UTC) + timedelta(days=5)).isoformat(),
        "customer_tier": 2,
        "penalty_cost": 25000,
        "margin_pct": 20,
        "quantity": 500,
    })
    assert "priority_breakdown" in result
    bd = result["priority_breakdown"]
    assert "urgency" in bd
    assert "customer_tier" in bd
    assert "penalty" in bd
    assert "margin" in bd
    assert "strategic_product" in bd
    assert "quantity" in bd
    total_breakdown = sum(bd.values())
    assert abs(result["priority_score"] - total_breakdown) < 0.01


def test_calculate_priority_custom_weights():
    custom_weights = {
        "priority_weights": {
            "urgency": 0.50,
            "customer_tier": 0.10,
            "penalty": 0.10,
            "margin": 0.10,
            "strategic_product": 0.10,
            "quantity": 0.10,
        },
    }
    default = calculate_priority({
        "required_date": (datetime.now(UTC) + timedelta(days=1)).isoformat(),
        "customer_tier": 1,
    })
    custom = calculate_priority({
        "required_date": (datetime.now(UTC) + timedelta(days=1)).isoformat(),
        "customer_tier": 1,
    }, tenant_config=custom_weights)
    assert custom["priority_score"] != default["priority_score"]


def test_calculate_priority_strategic_product():
    with_weights = {
        "priority_weights": {},
        "strategic_product_ids": ["prod-123"],
    }
    non_strategic = calculate_priority({
        "product_id": "prod-456",
        "required_date": (datetime.now(UTC) + timedelta(days=5)).isoformat(),
    }, tenant_config=with_weights)
    strategic = calculate_priority({
        "product_id": "prod-123",
        "required_date": (datetime.now(UTC) + timedelta(days=5)).isoformat(),
    }, tenant_config=with_weights)
    assert strategic["priority_score"] > non_strategic["priority_score"]


def test_calculate_priority_weights_normalized():
    bad_weights = {
        "priority_weights": {
            "urgency": 1.0,
            "customer_tier": 1.0,
            "penalty": 1.0,
            "margin": 1.0,
            "strategic_product": 1.0,
            "quantity": 1.0,
        },
    }
    result = calculate_priority({
        "required_date": (datetime.now(UTC) + timedelta(days=5)).isoformat(),
    }, tenant_config=bad_weights)
    assert 0.0 <= result["priority_score"] <= 1.0


def test_classify_eto():
    result = classify_demand_type(is_engineered=True)
    assert result["demand_type"] == "ETO"
    assert result["confidence"] > 0.9


def test_classify_mts_with_safety_stock():
    result = classify_demand_type(product_data={"safety_stock": 100, "source_type": "manufactured"})
    assert result["demand_type"] == "MTS"
