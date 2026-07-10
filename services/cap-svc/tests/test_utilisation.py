from app.core.utilisation import UtilisationCalculator


def test_utilisation_pct_handles_normal_case():
    assert UtilisationCalculator.utilisation_pct(45, 40) == 112.5


def test_utilisation_pct_handles_zero_capacity():
    assert UtilisationCalculator.utilisation_pct(10, 0) == 0.0


def test_is_overload_uses_threshold():
    assert UtilisationCalculator.is_overload(90, 90) is True
    assert UtilisationCalculator.is_overload(89.99, 90) is False


def test_overload_hours_only_positive_delta():
    assert UtilisationCalculator.overload_hours(48, 40) == 8.0
    assert UtilisationCalculator.overload_hours(32, 40) == 0.0
