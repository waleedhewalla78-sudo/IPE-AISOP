"""Unit tests for visual CPM engine."""

from datetime import UTC, datetime, timedelta

from app.core.visual_cpm import cascade_schedule, compute_critical_path, compute_slack


def _sample_operations():
    base = datetime(2026, 7, 1, 8, 0, tzinfo=UTC)
    return [
        {
            "operation_id": "op1",
            "mo_id": "mo1",
            "sequence": 10,
            "work_center_id": "wc1",
            "planned_start": base.isoformat(),
            "planned_end": (base + timedelta(minutes=60)).isoformat(),
            "duration_minutes": 60,
        },
        {
            "operation_id": "op2",
            "mo_id": "mo1",
            "sequence": 20,
            "work_center_id": "wc1",
            "planned_start": (base + timedelta(minutes=60)).isoformat(),
            "planned_end": (base + timedelta(minutes=180)).isoformat(),
            "duration_minutes": 120,
        },
        {
            "operation_id": "op3",
            "mo_id": "mo2",
            "sequence": 10,
            "work_center_id": "wc2",
            "planned_start": base.isoformat(),
            "planned_end": (base + timedelta(minutes=30)).isoformat(),
            "duration_minutes": 30,
        },
    ]


def test_compute_critical_path_returns_longest_chain():
    ops = _sample_operations()
    path = compute_critical_path(ops)
    assert "op1" in path
    assert "op2" in path
    assert len(path) >= 2


def test_compute_slack_non_negative():
    ops = _sample_operations()
    slack = compute_slack(ops)
    assert all(v >= 0 for v in slack.values())


def test_cascade_schedule_shifts_successors():
    ops = _sample_operations()
    result = cascade_schedule(
        ops,
        mo_id="mo1",
        operation_id="op1",
        delta_minutes=120,
    )
    shifted = {o["operation_id"]: o for o in result["operations"]}
    original_start = datetime.fromisoformat(ops[0]["planned_start"])
    new_start = datetime.fromisoformat(shifted["op1"]["planned_start"])
    assert (new_start - original_start).total_seconds() == 7200
    assert shifted["op2"]["is_critical"] is True
    assert "critical_path_ids" in result


def test_cascade_detects_wc_conflict():
    base = datetime(2026, 7, 1, 8, 0, tzinfo=UTC)
    ops = [
        {
            "operation_id": "a",
            "mo_id": "m1",
            "sequence": 1,
            "work_center_id": "wc1",
            "planned_start": base.isoformat(),
            "planned_end": (base + timedelta(minutes=120)).isoformat(),
        },
        {
            "operation_id": "b",
            "mo_id": "m2",
            "sequence": 1,
            "work_center_id": "wc1",
            "planned_start": (base + timedelta(minutes=60)).isoformat(),
            "planned_end": (base + timedelta(minutes=180)).isoformat(),
        },
    ]
    result = cascade_schedule(ops, mo_id="m2", operation_id="b", delta_minutes=0)
    assert len(result["conflicts"]) >= 1
