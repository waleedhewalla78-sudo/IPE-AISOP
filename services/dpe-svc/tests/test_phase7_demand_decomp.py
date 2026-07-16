"""Phase 7 §3 — Demand Deep core tests (decomposition / collaboration / NPI)."""

from app.core.phase7 import build_consensus, decompose_demand, forecast_npi


def test_decompose_components_and_forecast():
    data = decompose_demand(month=10, base=20, trend_per_month=2, months_from_base=1)
    comp = data["components"]
    assert comp["base"]["units"] == 20
    assert comp["trend"]["units"] == 2
    # October seasonal factor is 1.05 in the default index.
    assert comp["seasonal"]["factor"] == 1.05
    # 22 * 1.05 = 23.1 without promo/event.
    assert round(data["forecast_without_promo"], 1) == 23.1
    assert (
        data["confidence_interval_95"]["low"]
        <= data["forecast_units"]
        <= data["confidence_interval_95"]["high"]
    )


def test_decompose_promo_lift_positive_for_discount():
    data = decompose_demand(promo_active=True, promo_price_change_pct=-5.0, price_elasticity=-1.3)
    assert data["components"]["promotional"]["units"] > 0
    assert data["forecast_with_promo"] > data["forecast_without_promo"]


def test_consensus_weighted_and_disagreement_flag():
    data = build_consensus()
    assert data["consensus_units"] >= 1
    # Sales at 28 deviates >15% from ~24 consensus → flagged.
    flagged = {d["source"] for d in data["disagreement_flags"]}
    assert "sales" in flagged
    # Sales bias history 15% → weight decayed next cycle.
    assert any(b["source"] == "sales" for b in data["bias_tracking"])
    assert data["status"] == "needs_review"


def test_consensus_agreed_when_aligned():
    data = build_consensus(
        statistical=24,
        inputs=[{"source": "sales", "value": 24, "credibility": 1.0, "bias_history_pct": 2.0}],
    )
    assert data["disagreement_flags"] == []
    assert data["status"] == "agreed"


def test_npi_three_methods_and_composite():
    data = forecast_npi(months=12)
    methods = data["methods"]
    assert set(methods.keys()) == {"analogy", "cannibalization", "market_sizing"}
    assert len(data["composite_forecast"]) == 12
    # Cannibalization of the reference product begins month 3.
    m3 = next(c for c in data["composite_forecast"] if c["month"] == 3)
    assert m3["reference_cannibalization_units"] < 0
    m1 = next(c for c in data["composite_forecast"] if c["month"] == 1)
    assert m1["reference_cannibalization_units"] == 0
