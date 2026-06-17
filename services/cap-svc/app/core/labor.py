

def check_labor_availability(
    operator_id: str,
    shift_date: str,
    operator_data: dict | None = None,
) -> dict:
    if operator_data is None:
        operator_data = {}

    absence_prob = float(operator_data.get("predicted_absence_probability") or 0)
    max_consecutive = float(operator_data.get("max_consecutive_hours") or 10)
    is_overtime_eligible = bool(operator_data.get("overtime_eligible", True))

    available = absence_prob < 0.5

    return {
        "operator_id": operator_id,
        "date": shift_date,
        "available": available,
        "absence_probability": round(absence_prob, 4),
        "max_consecutive_hours": max_consecutive,
        "overtime_eligible": is_overtime_eligible,
        "max_available_hours": 8 + (4 if is_overtime_eligible and available else 0),
    }


def check_team_availability(
    shift_date: str,
    operators: list[dict],
    required_skills: list[str] | None = None,
) -> dict:
    available_ops = []
    for op in operators:
        result = check_labor_availability(
            operator_id=str(op.get("id", "")),
            shift_date=shift_date,
            operator_data=op,
        )
        if result["available"]:
            skills = op.get("skill_tags", [])
            if required_skills:
                has_skills = all(s in skills for s in required_skills)
                if not has_skills:
                    continue
            available_ops.append(result)

    return {
        "date": shift_date,
        "total_operators": len(operators),
        "available_operators": len(available_ops),
        "availability_pct": round(len(available_ops) / max(len(operators), 1) * 100, 1),
        "labor_shortage": len(available_ops) < 1,
        "operators": available_ops,
    }
