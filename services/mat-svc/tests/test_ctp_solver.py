import pytest
from app.core.ctp_solver import (
    CTPOrderLine,
    MaterialAvailability,
    CapacitySlot,
    check_material_feasibility,
    check_capacity_feasibility,
    binary_search_earliest_date,
    solve_ctp,
)


class TestCheckMaterialFeasibility:
    def test_feasible(self):
        materials = [
            MaterialAvailability("p1", 100.0, 50.0, 7),
        ]
        feasible, gaps, confidence = check_material_feasibility(
            CTPOrderLine("o1", "p1", 50, "2026-07-01"), materials
        )
        assert feasible is True
        assert len(gaps) == 0
        assert confidence == 1.0

    def test_infeasible_shortage(self):
        materials = [
            MaterialAvailability("p1", 10.0, 50.0, 7),
        ]
        feasible, gaps, confidence = check_material_feasibility(
            CTPOrderLine("o1", "p1", 50, "2026-07-01"), materials
        )
        assert feasible is False
        assert len(gaps) == 1
        assert confidence < 1.0

    def test_with_safety_stock(self):
        materials = [
            MaterialAvailability("p1", 60.0, 50.0, 7, safety_stock=20.0),
        ]
        feasible, gaps, confidence = check_material_feasibility(
            CTPOrderLine("o1", "p1", 50, "2026-07-01"), materials
        )
        assert feasible is False

    def test_empty_materials(self):
        feasible, gaps, confidence = check_material_feasibility(
            CTPOrderLine("o1", "p1", 50, "2026-07-01"), []
        )
        assert feasible is True


class TestCheckCapacityFeasibility:
    def test_feasible(self):
        slots = [
            CapacitySlot("wc1", "day_0", 8.0),
            CapacitySlot("wc1", "day_1", 8.0),
        ]
        feasible, gaps, confidence = check_capacity_feasibility(
            CTPOrderLine("o1", "p1", 10, "2026-07-01"), slots, 60.0
        )
        assert feasible is True

    def test_infeasible(self):
        slots = [
            CapacitySlot("wc1", "day_0", 1.0),
        ]
        feasible, gaps, confidence = check_capacity_feasibility(
            CTPOrderLine("o1", "p1", 100, "2026-07-01"), slots, 60.0
        )
        assert feasible is False
        assert len(gaps) == 1

    def test_empty_slots(self):
        feasible, gaps, confidence = check_capacity_feasibility(
            CTPOrderLine("o1", "p1", 10, "2026-07-01"), [], 60.0
        )
        assert feasible is False


class TestBinarySearchEarliestDate:
    def test_feasible_order(self):
        materials = [MaterialAvailability("p1", 100.0, 50.0, 7)]
        slots = [CapacitySlot("wc1", f"day_{i}", 8.0) for i in range(30)]
        result = binary_search_earliest_date(
            CTPOrderLine("o1", "p1", 50, "2026-07-01"), materials, slots
        )
        assert result.feasible is True
        assert result.confidence_score > 0

    def test_infeasible_material(self):
        materials = [MaterialAvailability("p1", 5.0, 50.0, 7)]
        slots = [CapacitySlot("wc1", f"day_{i}", 8.0) for i in range(30)]
        result = binary_search_earliest_date(
            CTPOrderLine("o1", "p1", 50, "2026-07-01"), materials, slots
        )
        assert result.feasible is False
        assert result.bottleneck == "material"

    def test_bottleneck_identified(self):
        materials = [MaterialAvailability("p1", 100.0, 50.0, 7)]
        slots = [CapacitySlot("wc1", "day_0", 0.5)]
        result = binary_search_earliest_date(
            CTPOrderLine("o1", "p1", 100, "2026-07-01"), materials, slots
        )
        assert result.bottleneck == "capacity"


class TestSolveCTP:
    def test_single_order(self):
        materials = [MaterialAvailability("p1", 100.0, 50.0, 7)]
        slots = [CapacitySlot("wc1", f"day_{i}", 8.0) for i in range(30)]
        orders = [CTPOrderLine("o1", "p1", 50, "2026-07-01")]
        results = solve_ctp(orders, materials, slots)
        assert len(results) == 1
        assert results[0].feasible is True

    def test_multiple_orders(self):
        materials = [MaterialAvailability("p1", 200.0, 100.0, 7)]
        slots = [CapacitySlot("wc1", f"day_{i}", 8.0) for i in range(30)]
        orders = [
            CTPOrderLine("o1", "p1", 50, "2026-07-01"),
            CTPOrderLine("o2", "p1", 50, "2026-07-02"),
        ]
        results = solve_ctp(orders, materials, slots)
        assert len(results) == 2

    def test_fallback_on_timeout(self):
        materials = [MaterialAvailability("p1", 100.0, 50.0, 7)]
        slots = [CapacitySlot("wc1", f"day_{i}", 8.0) for i in range(30)]
        orders = [CTPOrderLine("o1", "p1", 50, "2026-07-01")]
        results = solve_ctp(orders, materials, slots, timeout_seconds=0.001)
        assert len(results) == 1

    def test_empty_orders(self):
        results = solve_ctp([], [], [])
        assert len(results) == 0
