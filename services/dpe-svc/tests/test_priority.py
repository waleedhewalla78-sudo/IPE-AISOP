from datetime import UTC, datetime, timedelta

from app.core.priority import compute_priority_score


def test_returns_priority_score():
    result = compute_priority_score({"required_date": (datetime.now(UTC) + timedelta(days=10)).isoformat()})
    assert isinstance(result, dict)
    assert "priority_score" in result
    assert 0 <= result["priority_score"] <= 100


def test_high_urgency_scores_high():
    result = compute_priority_score({
        "required_date": (datetime.now(UTC) + timedelta(days=1)).isoformat(),
        "customer_tier": 1,
        "margin_pct": 30.0,
        "penalty_cost": 50000.0,
    })
    assert result["priority_score"] > 70


def test_low_urgency_scores_lower():
    result = compute_priority_score({
        "required_date": (datetime.now(UTC) + timedelta(days=90)).isoformat(),
        "customer_tier": 3,
        "margin_pct": 5.0,
        "penalty_cost": 0.0,
    })
    assert result["priority_score"] < 40


def test_customer_tier_scoring():
    tier1 = compute_priority_score({
        "required_date": (datetime.now(UTC) + timedelta(days=10)).isoformat(),
        "customer_tier": 1,
    })
    tier3 = compute_priority_score({
        "required_date": (datetime.now(UTC) + timedelta(days=10)).isoformat(),
        "customer_tier": 3,
    })
    assert tier1["priority_score"] > tier3["priority_score"]


def test_breakdown_contains_all_keys():
    result = compute_priority_score({
        "required_date": (datetime.now(UTC) + timedelta(days=5)).isoformat(),
        "customer_tier": 2,
        "margin_pct": 20.0,
        "penalty_cost": 10000.0,
    })
    bd = result["priority_breakdown"]
    for key in ("customer", "margin", "urgency", "strategic", "penalty"):
        assert key in bd


def test_custom_weights():
    custom = compute_priority_score({
        "required_date": (datetime.now(UTC) + timedelta(days=1)).isoformat(),
        "customer_tier": 1,
    }, tenant_config={"priority_weights": {"urgency": 0.50, "customer": 0.10,
                                            "margin": 0.10, "strategic": 0.10,
                                            "penalty": 0.20}})
    default = compute_priority_score({
        "required_date": (datetime.now(UTC) + timedelta(days=1)).isoformat(),
        "customer_tier": 1,
    })
    assert abs(custom["priority_score"] - default["priority_score"]) > 0.001


def test_strategic_product_boost():
    strategic = compute_priority_score({
        "required_date": (datetime.now(UTC) + timedelta(days=10)).isoformat(),
        "tags": ["strategic"],
    })
    normal = compute_priority_score({
        "required_date": (datetime.now(UTC) + timedelta(days=10)).isoformat(),
        "tags": [],
    })
    assert strategic["priority_score"] > normal["priority_score"]


def test_penalty_cost_scales():
    high_penalty = compute_priority_score({
        "required_date": (datetime.now(UTC) + timedelta(days=10)).isoformat(),
        "penalty_cost": 100000.0,
    })
    no_penalty = compute_priority_score({
        "required_date": (datetime.now(UTC) + timedelta(days=10)).isoformat(),
        "penalty_cost": 0.0,
    })
    assert high_penalty["priority_score"] > no_penalty["priority_score"]
