import pytest

from app.core.predictive_scorer import PredictiveRiskScorer, _score_to_color, _calculate_trend
from app.core.root_cause_analyzer import RootCauseAnalyzer


@pytest.mark.asyncio
async def test_predictive_scorer_horizons():
    scorer = PredictiveRiskScorer()
    result = await scorer.score_future(None, "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11", "mo-1")
    assert result["current"]["score"] is not None
    assert set(result["predictions"].keys()) == {3, 7, 14}
    assert result["trend"] in ("stable", "deteriorating", "improving", "crisis_approaching")
    assert "recommended_action" in result


def test_score_to_color():
    assert _score_to_color(90) == "green"
    assert _score_to_color(60) == "amber"
    assert _score_to_color(40) == "red"


def test_trend_crisis():
    preds = {
        3: {"predicted_score": 72},
        7: {"predicted_score": 45},
        14: {"predicted_score": 40},
    }
    assert _calculate_trend(88, preds) == "crisis_approaching"


@pytest.mark.asyncio
async def test_root_cause_chain_depth():
    analyzer = RootCauseAnalyzer()
    chain = await analyzer.analyze(
        None,
        "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
        "mo-1",
        gate_scores={"capacity": 40, "material": 70, "delivery": 80, "bom": 100, "demand": 95},
    )
    assert len(chain.levels) >= 2
    assert chain.root_cause is not None
    assert len(chain.recommendations) >= 1
    payload = chain.to_dict()
    assert payload["chain"]
    assert payload["chain_depth"] >= 2
