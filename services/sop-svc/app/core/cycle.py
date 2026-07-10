VALID_TRANSITIONS: dict[str, str] = {
    "draft": "demand_review",
    "demand_review": "supply_review",
    "supply_review": "reconciliation",
    "reconciliation": "management_review",
    "management_review": "closed",
}


def validate_transition(current_status: str, next_status: str) -> None:
    expected = VALID_TRANSITIONS.get(current_status)
    if expected != next_status:
        raise ValueError(f"Invalid S&OP transition: {current_status} -> {next_status}")


def advance_status(current_status: str) -> str:
    next_status = VALID_TRANSITIONS.get(current_status)
    if not next_status:
        raise ValueError(f"Cannot advance S&OP cycle from {current_status}")
    return next_status
