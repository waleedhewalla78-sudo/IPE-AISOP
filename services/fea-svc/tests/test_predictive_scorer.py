"""Unit tests — PredictiveRiskScorer (no DB)."""

import pytest

from app.core.predictive_scorer import PredictiveRiskScorer, _calculate_trend, _score_to_color


def test_score_to_color_thresholds():
    assert _score_to_color(90) == "green"
    assert _score_to_color(60) == "amber"
    assert _score_to_color(40) == "red"


def test_calculate_trend_crisis_and_deteriorating():
    preds = {
        3: {"predicted_score": 75},
        7: {"predicted_score": 55},
        14: {"predicted_score": 40},
    }
    assert _calculate_trend(85, preds) == "crisis_approaching"
    preds2 = {
        3: {"predicted_score": 70},
        7: {"predicted_score": 60},
        14: {"predicted_score": 50},
    }
    assert _calculate_trend(80, preds2) == "deteriorating"


@pytest.mark.asyncio
async def test_score_future_offline_horizons():
    scorer = PredictiveRiskScorer()
    result = await scorer.score_future(None, "11111111-1111-1111-1111-111111111111", "22222222-2222-2222-2222-222222222222")
    assert set(result["predictions"].keys()) == {3, 7, 14}
    assert "trend" in result
    assert "recommended_action" in result
    assert result["current"]["score"] > 0
    for h in (3, 7, 14):
        assert "predicted_score" in result["predictions"][h]
        assert "primary_risk" in result["predictions"][h]
