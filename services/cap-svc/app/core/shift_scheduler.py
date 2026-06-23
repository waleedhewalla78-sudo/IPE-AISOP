from datetime import datetime, timedelta


def generate_worker_availability_intervals(
    shift_rules: list[dict],
    planning_horizon_minutes: int = 168 * 60,
    reference_date: datetime | None = None,
) -> list[tuple[int, int]]:
    """Convert shift rules into available time windows for the solver.

    Args:
        shift_rules: List of shift rule dicts with keys:
            - days_of_week: list of ints (0=Mon, 6=Sun)
            - start_hour, start_minute: shift start time
            - end_hour, end_minute: shift end time
            - break_minutes: break duration (subtracted from availability)
        planning_horizon_minutes: Total planning horizon in minutes.
        reference_date: Starting datetime for interval generation.

    Returns:
        List of (start_minute, end_minute) tuples relative to reference_date.
    """
    if not shift_rules:
        return [(0, planning_horizon_minutes)]

    if reference_date is None:
        reference_date = datetime(2026, 1, 5, 0, 0, 0)

    intervals: list[tuple[int, int]] = []
    current = reference_date
    horizon_end = reference_date + timedelta(minutes=planning_horizon_minutes)

    while current < horizon_end:
        weekday = current.weekday()

        for rule in shift_rules:
            days = rule.get("days_of_week", [0, 1, 2, 3, 4])
            if weekday not in days:
                continue

            start_h = rule.get("start_hour", 8)
            start_m = rule.get("start_minute", 0)
            end_h = rule.get("end_hour", 16)
            end_m = rule.get("end_minute", 0)
            break_mins = rule.get("break_minutes", 30)

            day_start = current.replace(hour=start_h, minute=start_m, second=0, microsecond=0)
            day_end = current.replace(hour=end_h, minute=end_m, second=0, microsecond=0)

            if day_start < reference_date:
                day_start = reference_date
            if day_end > horizon_end:
                day_end = horizon_end

            if day_start >= day_end:
                continue

            shift_duration = int((day_end - day_start).total_seconds() / 60)
            if shift_duration <= break_mins:
                continue

            start_min = int((day_start - reference_date).total_seconds() / 60)
            mid = start_min + shift_duration // 2
            intervals.append((start_min, mid))
            intervals.append((mid + break_mins, start_min + shift_duration))

        current += timedelta(days=1)

    intervals.sort(key=lambda x: x[0])
    return intervals


def merge_intervals(intervals: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """Merge overlapping or adjacent intervals."""
    if not intervals:
        return []

    sorted_ints = sorted(intervals, key=lambda x: x[0])
    merged = [sorted_ints[0]]

    for start, end in sorted_ints[1:]:
        if start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))

    return merged


def worker_has_skill(worker_skills: list[str], required_skill_id: str | None, required_skill_tags: list[str]) -> bool:
    """Check if a worker has the required skill for an operation.

    Args:
        worker_skills: List of skill names/tags the worker possesses.
        required_skill_id: Specific skill UUID required (from RoutingOperation.required_skill_id).
        required_skill_tags: List of skill tag strings (from RoutingOperation.required_skill_tags).

    Returns:
        True if worker matches requirements.
    """
    if not required_skill_id and not required_skill_tags:
        return True

    if required_skill_id:
        if required_skill_id in worker_skills:
            return True

    if required_skill_tags:
        if all(tag in worker_skills for tag in required_skill_tags):
            return True

    return False
