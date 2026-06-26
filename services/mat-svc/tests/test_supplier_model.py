"""Unit tests for supplier delay prediction (AG-02 / P8 mat-svc)."""

from datetime import UTC, datetime
from decimal import Decimal

from app.core.supplier_model import adjust_expected_date, predict_delay


class TestPredictDelay:
    def test_none_inputs_returns_zeros(self):
        result = predict_delay(None, None, None)
        assert result["expected_delay_days"] == 0.0
        assert result["confidence"] == 0.0

    def test_normal_distribution(self):
        result = predict_delay(Decimal("2"), Decimal("0.5"), Decimal("0.8"))
        assert result["expected_delay_days"] >= 0
        assert result["p10"] <= result["p50"] <= result["p90"]
        assert 0 < result["confidence"] <= 0.99

    def test_lognormal_distribution(self):
        result = predict_delay(
            Decimal("3"), Decimal("1"), Decimal("0.7"), distribution_type="lognormal"
        )
        assert result["expected_delay_days"] >= 0
        assert result["p90"] >= result["p10"]

    def test_zero_std_dev_uses_minimum(self):
        result = predict_delay(Decimal("5"), Decimal("0"), Decimal("0.5"))
        assert result["delay_std_dev"] == 0.0


class TestAdjustExpectedDate:
    def test_adjusts_with_delay(self):
        base = datetime(2026, 6, 1, tzinfo=UTC)
        result = adjust_expected_date(base, Decimal("2"), Decimal("0.5"))
        assert "adjusted_date" in result
        assert "p90_date" in result
        assert result["expected_delay_days"] >= 0

    def test_no_delay_when_none(self):
        base = datetime(2026, 6, 1, tzinfo=UTC)
        result = adjust_expected_date(base, None, None)
        assert result["adjusted_date"] == base.isoformat()
