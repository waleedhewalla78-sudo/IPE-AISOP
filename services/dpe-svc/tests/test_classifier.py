"""Demand classifier unit tests — R2-03."""

from app.core.classifier import classify_demand_type


def test_classify_eto():
    result = classify_demand_type(is_engineered=True)
    assert result["demand_type"] == "ETO"
    assert result["confidence"] == 0.95


def test_classify_cto():
    result = classify_demand_type(is_customized=True)
    assert result["demand_type"] == "CTO"


def test_classify_mto_tier():
    result = classify_demand_type(customer_tier=1)
    assert result["demand_type"] == "MTO"


def test_classify_mts_safety_stock():
    result = classify_demand_type(product_data={"safety_stock": 100})
    assert result["demand_type"] == "MTS"


def test_classify_mts_low_cv():
    result = classify_demand_type(product_data={"demand_cv": 0.3})
    assert result["demand_type"] == "MTS"


def test_classify_purchased_mto():
    result = classify_demand_type(product_data={"source_type": "purchased"})
    assert result["demand_type"] == "MTO"


def test_classify_default_mto():
    result = classify_demand_type()
    assert result["demand_type"] == "MTO"
    assert result["confidence"] == 0.6
