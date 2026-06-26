"""Labor availability unit tests — R2-01."""

from app.core.labor import check_labor_availability, check_team_availability


def test_labor_unavailable_high_absence():
    result = check_labor_availability("op1", "2026-06-01", {"predicted_absence_probability": 0.8})
    assert result["available"] is False
    assert result["max_available_hours"] == 8


def test_labor_overtime_eligible():
    result = check_labor_availability(
        "op2", "2026-06-01", {"predicted_absence_probability": 0.1, "overtime_eligible": True}
    )
    assert result["available"] is True
    assert result["max_available_hours"] == 12


def test_team_availability_skill_filter():
    operators = [
        {"id": "a", "predicted_absence_probability": 0.1, "skill_tags": ["welding"]},
        {"id": "b", "predicted_absence_probability": 0.1, "skill_tags": ["assembly"]},
    ]
    result = check_team_availability("2026-06-01", operators, required_skills=["welding"])
    assert result["available_operators"] == 1
    assert result["labor_shortage"] is False
