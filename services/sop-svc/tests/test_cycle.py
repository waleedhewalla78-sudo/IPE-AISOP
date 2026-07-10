import pytest

from app.core.cycle import advance_status, validate_transition


def test_valid_cycle_transitions():
    status = "draft"
    for expected in [
        "demand_review",
        "supply_review",
        "reconciliation",
        "management_review",
        "closed",
    ]:
        validate_transition(status, expected)
        status = advance_status(status)
        assert status == expected


def test_invalid_cycle_transition_raises():
    with pytest.raises(ValueError):
        validate_transition("draft", "management_review")


def test_closed_cycle_cannot_advance():
    with pytest.raises(ValueError):
        advance_status("closed")
