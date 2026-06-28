from app.core.promising import compute_atp_promise


def test_atp_in_stock():
    result = compute_atp_promise(10, 100)
    assert result["promise_type"] == "ATP"
    assert result["confidence_score"] >= 0.9


def test_ctp_shortfall():
    result = compute_atp_promise(100, 10)
    assert result["promise_type"] == "CTP"
    assert result.get("shortfall", 0) > 0
