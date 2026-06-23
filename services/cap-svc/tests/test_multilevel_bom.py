"""Tests for multi-level BOM scheduling and phantom subassembly explosion."""

from app.core.scheduler import explode_phantom_boms, solve_schedule

WORK_CENTERS = [{"id": "WC001", "name": "Assembly", "capacity_hours_per_day": 16, "oee": 0.9}]


def test_explode_phantom_boms_removes_phantom_children():
    """Phantom BOM nodes are removed and their children are promoted."""
    operations = [
        {"id": "OP001", "mo_id": "MO001", "sequence": 1, "work_center_id": "WC001",
         "duration_planned_mins": 60, "bom_level": 0, "is_phantom": False},
        {"id": "OP002", "mo_id": "MO001", "sequence": 2, "work_center_id": "WC001",
         "duration_planned_mins": 30, "parent_operation_id": "OP001",
         "bom_level": 1, "is_phantom": True},
        {"id": "OP003", "mo_id": "MO001", "sequence": 3, "work_center_id": "WC001",
         "duration_planned_mins": 45, "parent_operation_id": "OP002",
         "bom_level": 2, "is_phantom": False},
    ]

    result = explode_phantom_boms(operations)

    op_ids = {op["id"] for op in result}
    assert "OP002" not in op_ids
    assert "OP003" in op_ids
    assert "OP001" in op_ids


def test_explode_phantom_boms_promotes_children():
    """Children of phantom ops are promoted to be children of the phantom's parent."""
    operations = [
        {"id": "ROOT", "mo_id": "MO001", "sequence": 1, "work_center_id": "WC001",
         "duration_planned_mins": 100, "bom_level": 0, "is_phantom": False},
        {"id": "PHANTOM", "mo_id": "MO001", "sequence": 2, "work_center_id": "WC001",
         "duration_planned_mins": 50, "bom_level": 1, "is_phantom": True,
         "parent_operation_id": "ROOT"},
        {"id": "CHILD", "mo_id": "MO001", "sequence": 3, "work_center_id": "WC001",
         "duration_planned_mins": 30, "bom_level": 2, "is_phantom": False,
         "parent_operation_id": "PHANTOM"},
    ]

    result = explode_phantom_boms(operations)

    op_ids = {op["id"] for op in result}
    assert "ROOT" in op_ids
    assert "PHANTOM" not in op_ids
    assert "CHILD" in op_ids
    assert len(result) == 2


def test_explode_phantom_boms_no_phantoms_unchanged():
    """Non-phantom operations should pass through unchanged."""
    operations = [
        {"id": "OP001", "mo_id": "MO001", "sequence": 1, "work_center_id": "WC001",
         "duration_planned_mins": 60, "bom_level": 0, "is_phantom": False},
        {"id": "OP002", "mo_id": "MO001", "sequence": 2, "work_center_id": "WC001",
         "duration_planned_mins": 30, "bom_level": 0, "is_phantom": False},
    ]

    result = explode_phantom_boms(operations)

    assert len(result) == 2
    assert result[0]["id"] == "OP001"
    assert result[1]["id"] == "OP002"


def test_explode_phantom_boms_depth_exceeded_inflates_duration():
    """Operations beyond max_depth get 10% duration inflation."""
    operations = [
        {"id": "ROOT", "mo_id": "MO001", "sequence": 1, "work_center_id": "WC001",
         "duration_planned_mins": 100, "bom_level": 0, "is_phantom": False},
        {"id": "L1", "mo_id": "MO001", "sequence": 2, "work_center_id": "WC001",
         "duration_planned_mins": 50, "parent_operation_id": "ROOT",
         "bom_level": 1, "is_phantom": True},
        {"id": "L2", "mo_id": "MO001", "sequence": 3, "work_center_id": "WC001",
         "duration_planned_mins": 30, "parent_operation_id": "L1",
         "bom_level": 2, "is_phantom": False},
    ]

    result = explode_phantom_boms(operations, max_depth=1)

    l2_op = next((op for op in result if op["id"] == "L2"), None)
    assert l2_op is not None
    assert l2_op["duration_planned_mins"] == int(30 * 1.1)


def test_multilevel_precedence_with_transfer_time():
    """Child operations must complete before parent starts, plus transfer time."""
    operations = [
        {"id": "CHILD1", "mo_id": "MO001", "sequence": 1, "work_center_id": "WC001",
         "duration_planned_mins": 30, "bom_level": 1, "is_phantom": False,
         "parent_operation_id": "PARENT", "transfer_time_mins": 15},
        {"id": "CHILD2", "mo_id": "MO001", "sequence": 2, "work_center_id": "WC001",
         "duration_planned_mins": 45, "bom_level": 1, "is_phantom": False,
         "parent_operation_id": "PARENT", "transfer_time_mins": 15},
        {"id": "PARENT", "mo_id": "MO001", "sequence": 3, "work_center_id": "WC001",
         "duration_planned_mins": 60, "bom_level": 0, "is_phantom": False,
         "parent_operation_id": None, "transfer_time_mins": 0},
    ]

    result = solve_schedule(WORK_CENTERS, operations, horizon=1000, solver_timeout_seconds=10)

    assert result["status"] in ("OPTIMAL", "FEASIBLE")
    assignments = {a["operation_id"]: a for a in result["assignments"]}

    for child_id in ["CHILD1", "CHILD2"]:
        child = assignments[child_id]
        parent = assignments["PARENT"]
        assert parent["start_minute"] >= child["end_minute"] + 15, (
            f"Parent started at {parent['start_minute']} but child {child_id} "
            f"ended at {child['end_minute']} + 15 transfer = {child['end_minute'] + 15}"
        )


def test_multilevel_bom_scheduling_produces_valid_schedule():
    """Multi-level BOM with phantom subassembly produces valid schedule."""
    operations = [
        {"id": "SUB1", "mo_id": "MO001", "sequence": 1, "work_center_id": "WC001",
         "duration_planned_mins": 60, "bom_level": 1, "is_phantom": False,
         "parent_operation_id": "ASSEMBLY", "transfer_time_mins": 10,
         "due_date_minutes": 500, "priority_score": 0.9},
        {"id": "SUB2", "mo_id": "MO001", "sequence": 2, "work_center_id": "WC001",
         "duration_planned_mins": 90, "bom_level": 1, "is_phantom": False,
         "parent_operation_id": "ASSEMBLY", "transfer_time_mins": 10,
         "due_date_minutes": 500, "priority_score": 0.9},
        {"id": "ASSEMBLY", "mo_id": "MO001", "sequence": 3, "work_center_id": "WC001",
         "duration_planned_mins": 120, "bom_level": 0, "is_phantom": False,
         "parent_operation_id": None, "transfer_time_mins": 0,
         "due_date_minutes": 500, "priority_score": 0.9},
    ]

    result = solve_schedule(WORK_CENTERS, operations, horizon=1000, solver_timeout_seconds=10)

    assert result["status"] in ("OPTIMAL", "FEASIBLE")
    assert len(result["assignments"]) == 3

    assignments = sorted(result["assignments"], key=lambda a: a["start_minute"])
    for i in range(len(assignments) - 1):
        assert assignments[i]["end_minute"] <= assignments[i + 1]["start_minute"], (
            f"Overlap: {assignments[i]['operation_id']} ends at {assignments[i]['end_minute']} "
            f"but {assignments[i+1]['operation_id']} starts at {assignments[i+1]['start_minute']}"
        )


def test_multiple_mos_with_independent_bom_levels():
    """Multiple MOs with different BOM depths schedule independently."""
    work_centers = [
        {"id": "WC001", "name": "Assembly", "capacity_hours_per_day": 16, "oee": 0.9},
        {"id": "WC002", "name": "Machining", "capacity_hours_per_day": 16, "oee": 0.9},
    ]
    operations = [
        {"id": "MO1-OP1", "mo_id": "MO001", "sequence": 1, "work_center_id": "WC001",
         "duration_planned_mins": 60, "bom_level": 0, "is_phantom": False,
         "due_date_minutes": 300, "priority_score": 0.9},
        {"id": "MO1-OP2", "mo_id": "MO001", "sequence": 2, "work_center_id": "WC002",
         "duration_planned_mins": 45, "bom_level": 0, "is_phantom": False,
         "due_date_minutes": 300, "priority_score": 0.9},
        {"id": "MO2-OP2", "mo_id": "MO002", "sequence": 1, "work_center_id": "WC001",
         "duration_planned_mins": 30, "bom_level": 1, "is_phantom": False,
         "parent_operation_id": "MO2-OP1", "transfer_time_mins": 5,
         "due_date_minutes": 600, "priority_score": 0.5},
        {"id": "MO2-OP1", "mo_id": "MO002", "sequence": 2, "work_center_id": "WC001",
         "duration_planned_mins": 90, "bom_level": 0, "is_phantom": False,
         "due_date_minutes": 600, "priority_score": 0.5},
    ]

    result = solve_schedule(work_centers, operations, horizon=1000, solver_timeout_seconds=10)

    assert result["status"] in ("OPTIMAL", "FEASIBLE")
    assert len(result["assignments"]) == 4

    assignments = {a["operation_id"]: a for a in result["assignments"]}
    assert assignments["MO2-OP1"]["start_minute"] >= assignments["MO2-OP2"]["end_minute"] + 5


def test_frozen_ops_with_multilevel_bom():
    """Frozen operations remain fixed while BOM children schedule around them."""
    operations = [
        {"id": "CHILD1", "mo_id": "MO001", "sequence": 1, "work_center_id": "WC001",
         "duration_planned_mins": 30, "bom_level": 1, "is_phantom": False,
         "parent_operation_id": "PARENT", "transfer_time_mins": 10,
         "due_date_minutes": 500, "priority_score": 0.9},
        {"id": "CHILD2", "mo_id": "MO001", "sequence": 2, "work_center_id": "WC001",
         "duration_planned_mins": 45, "bom_level": 1, "is_phantom": False,
         "parent_operation_id": "PARENT", "transfer_time_mins": 10,
         "due_date_minutes": 500, "priority_score": 0.9},
        {"id": "PARENT", "mo_id": "MO001", "sequence": 3, "work_center_id": "WC001",
         "duration_planned_mins": 60, "bom_level": 0, "is_phantom": False,
         "due_date_minutes": 500, "priority_score": 0.9},
    ]
    frozen = [{"operation_id": "PARENT", "fixed_start": 200, "fixed_end": 260}]

    result = solve_schedule(WORK_CENTERS, operations, horizon=1000, solver_timeout_seconds=10,
                            frozen_ops=frozen)

    assert result["status"] in ("OPTIMAL", "FEASIBLE")
    parent = next(a for a in result["assignments"] if a["operation_id"] == "PARENT")
    assert parent["start_minute"] == 200
    assert parent["end_minute"] == 260


def test_max_bom_depth_configurable():
    """MAX_BOM_DEPTH can be overridden via solve_schedule parameter."""
    operations = [
        {"id": "L0", "mo_id": "MO001", "sequence": 1, "work_center_id": "WC001",
         "duration_planned_mins": 100, "bom_level": 0, "is_phantom": False},
        {"id": "L1", "mo_id": "MO001", "sequence": 2, "work_center_id": "WC001",
         "duration_planned_mins": 50, "bom_level": 1, "is_phantom": True,
         "parent_operation_id": "L0"},
        {"id": "L2", "mo_id": "MO001", "sequence": 3, "work_center_id": "WC001",
         "duration_planned_mins": 30, "bom_level": 2, "is_phantom": False,
         "parent_operation_id": "L1"},
    ]

    result = solve_schedule(WORK_CENTERS, operations, horizon=1000, solver_timeout_seconds=10,
                            max_bom_depth=1)

    assert result["status"] in ("OPTIMAL", "FEASIBLE")


def test_empty_operations_returns_infeasible():
    """Empty operations list should return INFEASIBLE (no assignments)."""
    result = solve_schedule(WORK_CENTERS, [], horizon=1000, solver_timeout_seconds=5)
    assert result["status"] == "INFEASIBLE"
    assert len(result["assignments"]) == 0


def test_assignments_contain_bom_level_and_parent():
    """Solver output includes bom_level and parent_operation_id fields."""
    operations = [
        {"id": "CHILD", "mo_id": "MO001", "sequence": 1, "work_center_id": "WC001",
         "duration_planned_mins": 30, "bom_level": 1, "is_phantom": False,
         "parent_operation_id": "PARENT", "transfer_time_mins": 10},
        {"id": "PARENT", "mo_id": "MO001", "sequence": 2, "work_center_id": "WC001",
         "duration_planned_mins": 60, "bom_level": 0, "is_phantom": False,
         "parent_operation_id": None, "transfer_time_mins": 0},
    ]

    result = solve_schedule(WORK_CENTERS, operations, horizon=1000, solver_timeout_seconds=10)

    assert result["status"] in ("OPTIMAL", "FEASIBLE")
    assignments = {a["operation_id"]: a for a in result["assignments"]}
    assert assignments["PARENT"]["bom_level"] == 0
    assert assignments["PARENT"]["parent_operation_id"] is None
    assert assignments["CHILD"]["bom_level"] == 1
    assert assignments["CHILD"]["parent_operation_id"] == "PARENT"


def test_phantom_with_nested_children_flattened():
    """Deeply nested phantom BOMs are fully flattened."""
    operations = [
        {"id": "ROOT", "mo_id": "MO001", "sequence": 1, "work_center_id": "WC001",
         "duration_planned_mins": 100, "bom_level": 0, "is_phantom": False},
        {"id": "PH1", "mo_id": "MO001", "sequence": 2, "work_center_id": "WC001",
         "duration_planned_mins": 50, "bom_level": 1, "is_phantom": True,
         "parent_operation_id": "ROOT"},
        {"id": "PH2", "mo_id": "MO001", "sequence": 3, "work_center_id": "WC001",
         "duration_planned_mins": 30, "bom_level": 2, "is_phantom": True,
         "parent_operation_id": "PH1"},
        {"id": "LEAF", "mo_id": "MO001", "sequence": 4, "work_center_id": "WC001",
         "duration_planned_mins": 20, "bom_level": 3, "is_phantom": False,
         "parent_operation_id": "PH2"},
    ]

    result = explode_phantom_boms(operations)

    op_ids = {op["id"] for op in result}
    assert "ROOT" in op_ids
    assert "PH1" not in op_ids
    assert "PH2" not in op_ids
    assert "LEAF" in op_ids
    assert len(result) == 2


def test_transfer_time_zero_when_not_specified():
    """Operations without transfer_time_mins default to 0."""
    operations = [
        {"id": "CHILD", "mo_id": "MO001", "sequence": 1, "work_center_id": "WC001",
         "duration_planned_mins": 30, "bom_level": 1, "is_phantom": False,
         "parent_operation_id": "PARENT"},
        {"id": "PARENT", "mo_id": "MO001", "sequence": 2, "work_center_id": "WC001",
         "duration_planned_mins": 60, "bom_level": 0, "is_phantom": False,
         "parent_operation_id": None},
    ]

    result = solve_schedule(WORK_CENTERS, operations, horizon=1000, solver_timeout_seconds=10)

    assert result["status"] in ("OPTIMAL", "FEASIBLE")
    assignments = {a["operation_id"]: a for a in result["assignments"]}
    assert assignments["PARENT"]["start_minute"] >= assignments["CHILD"]["end_minute"]
