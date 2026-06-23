"""Tests for worker constraints, skill matching, and shift scheduling."""

from app.core.scheduler import (
    explode_phantom_boms,
    solve_schedule,
    _build_worker_skill_map,
    _match_worker_to_operation,
)
from app.core.shift_scheduler import (
    generate_worker_availability_intervals,
    merge_intervals,
    worker_has_skill,
)


class TestWorkerSkillMap:
    def test_build_worker_skill_map(self):
        workers = [
            {"id": "w1", "skill_ids": ["s1", "s2"], "skill_tags": ["welding"]},
            {"id": "w2", "skill_ids": ["s3"], "skill_tags": []},
        ]
        result = _build_worker_skill_map(workers)
        assert result["w1"] == {"s1", "s2", "welding"}
        assert result["w2"] == {"s3"}

    def test_empty_workers(self):
        result = _build_worker_skill_map([])
        assert result == {}


class TestMatchWorkerToOperation:
    def setup_method(self):
        self.worker_skills = {
            "w1": {"s1", "welding"},
            "w2": {"s2"},
            "w3": set(),
        }

    def test_no_requirements_matches_any(self):
        assert _match_worker_to_operation("w1", self.worker_skills, None, []) is True
        assert _match_worker_to_operation("w3", self.worker_skills, None, []) is True

    def test_skill_id_match(self):
        assert _match_worker_to_operation("w1", self.worker_skills, "s1", []) is True
        assert _match_worker_to_operation("w2", self.worker_skills, "s1", []) is False

    def test_skill_tags_match(self):
        assert _match_worker_to_operation("w1", self.worker_skills, None, ["welding"]) is True
        assert _match_worker_to_operation("w2", self.worker_skills, None, ["welding"]) is False

    def test_both_skill_id_and_tags(self):
        # Worker has skill_id s1 AND tag welding - both match
        assert _match_worker_to_operation("w1", self.worker_skills, "s1", ["welding"]) is True
        # Worker has tag welding but not skill_id s2 - OR logic means tag match is sufficient
        assert _match_worker_to_operation("w1", self.worker_skills, "s2", ["welding"]) is True
        # Worker has neither matching skill_id nor tags
        assert _match_worker_to_operation("w3", self.worker_skills, "s2", ["welding"]) is False


class TestShiftScheduler:
    def test_generate_empty_shifts(self):
        intervals = generate_worker_availability_intervals([], 168 * 60)
        assert len(intervals) == 1
        assert intervals[0] == (0, 168 * 60)

    def test_generate_weekday_shift(self):
        shift_rules = [{"days_of_week": [0, 1, 2, 3, 4], "start_hour": 8, "end_hour": 16, "break_minutes": 30}]
        intervals = generate_worker_availability_intervals(shift_rules, 5 * 24 * 60)
        assert len(intervals) > 0
        for start, end in intervals:
            assert start < end

    def test_merge_intervals(self):
        intervals = [(0, 100), (50, 200), (300, 400)]
        merged = merge_intervals(intervals)
        assert merged == [(0, 200), (300, 400)]

    def test_worker_has_skill_no_requirements(self):
        assert worker_has_skill(["welding"], None, []) is True

    def test_worker_has_skill_by_id(self):
        assert worker_has_skill(["s1", "s2"], "s1", []) is True
        assert worker_has_skill(["s1", "s2"], "s3", []) is False

    def test_worker_has_skill_by_tags(self):
        assert worker_has_skill(["welding", "cutting"], None, ["welding"]) is True
        assert worker_has_skill(["welding"], None, ["welding", "cutting"]) is False


class TestWorkerConstraints:
    def test_no_workers_still_solves(self):
        work_centers = [{"id": "WC1", "capacity_hours_per_day": 8}]
        operations = [
            {"id": "OP1", "mo_id": "MO1", "sequence": 1, "work_center_id": "WC1",
             "duration_planned_mins": 60, "due_date_minutes": 200},
        ]
        result = solve_schedule(work_centers, operations, horizon=500, solver_timeout_seconds=10)
        assert result["status"] in ("OPTIMAL", "FEASIBLE")
        assert len(result["assignments"]) == 1

    def test_workers_without_skill_constraints(self):
        work_centers = [{"id": "WC1", "capacity_hours_per_day": 8}]
        operations = [
            {"id": "OP1", "mo_id": "MO1", "sequence": 1, "work_center_id": "WC1",
             "duration_planned_mins": 60, "due_date_minutes": 200, "requires_operator": False},
        ]
        workers = [{"id": "W1", "skill_ids": [], "skill_tags": [], "shift_rules": []}]
        result = solve_schedule(work_centers, operations, horizon=500, solver_timeout_seconds=10, workers=workers)
        assert result["status"] in ("OPTIMAL", "FEASIBLE")

    def test_workers_with_matching_skills(self):
        work_centers = [{"id": "WC1", "capacity_hours_per_day": 8}]
        operations = [
            {"id": "OP1", "mo_id": "MO1", "sequence": 1, "work_center_id": "WC1",
             "duration_planned_mins": 60, "due_date_minutes": 200,
             "required_skill_id": "skill_weld", "requires_operator": True},
        ]
        workers = [{"id": "W1", "skill_ids": ["skill_weld"], "skill_tags": [], "shift_rules": []}]
        result = solve_schedule(work_centers, operations, horizon=500, solver_timeout_seconds=10, workers=workers)
        assert result["status"] in ("OPTIMAL", "FEASIBLE")

    def test_workers_without_matching_skills_still_solves(self):
        """When no worker has the required skill, Phase 1 has zero eligible workers
        per operation so the must-have-worker constraint is never added. The solver
        schedules without workers. Phase 2 relaxation is triggered when there ARE
        eligible workers but not enough to cover all concurrent operations."""
        work_centers = [{"id": "WC1", "capacity_hours_per_day": 8}]
        operations = [
            {"id": "OP1", "mo_id": "MO1", "sequence": 1, "work_center_id": "WC1",
             "duration_planned_mins": 60, "due_date_minutes": 200,
             "required_skill_id": "skill_weld", "requires_operator": True},
        ]
        workers = [{"id": "W1", "skill_ids": ["skill_cnc"], "skill_tags": [], "shift_rules": []}]
        result = solve_schedule(work_centers, operations, horizon=500, solver_timeout_seconds=10, workers=workers)
        assert result["status"] in ("OPTIMAL", "FEASIBLE")
        # No eligible workers → constraint not added → no relaxation needed
        assert result.get("skill_relaxed") is False

    def test_skill_relaxation_fallback(self):
        """Test that when Phase 1 (enforce_skills=True) fails with INFEASIBLE,
        Phase 2 (enforce_skills=False) finds a solution and marks skill_relaxed=True.

        Two operations on different work centers both require skill_weld, both
        must complete by minute 480, and each takes 480 minutes. With only one
        skilled worker, the worker can't cover both in the time window."""
        work_centers = [
            {"id": "WC1", "capacity_hours_per_day": 8},
            {"id": "WC2", "capacity_hours_per_day": 8},
        ]
        operations = [
            {"id": "OP1", "mo_id": "MO1", "sequence": 1, "work_center_id": "WC1",
             "duration_planned_mins": 480, "due_date_minutes": 480,
             "required_skill_id": "skill_weld", "requires_operator": True},
            {"id": "OP2", "mo_id": "MO2", "sequence": 1, "work_center_id": "WC2",
             "duration_planned_mins": 480, "due_date_minutes": 480,
             "required_skill_id": "skill_weld", "requires_operator": True},
        ]
        workers = [{"id": "W1", "skill_ids": ["skill_weld"], "skill_tags": [], "shift_rules": []}]
        result = solve_schedule(work_centers, operations, horizon=600, solver_timeout_seconds=5, workers=workers)
        assert result["status"] in ("OPTIMAL", "FEASIBLE")
        assert result.get("skill_relaxed") is True
        assert result.get("requires_manual_skill_verification") is True
