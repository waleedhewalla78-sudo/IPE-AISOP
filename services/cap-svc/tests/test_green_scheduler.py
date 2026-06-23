import pytest
from app.core.scheduler_green import (
    EmissionFactorData,
    MaterialCarbonData,
    TransportEmissionData,
    calculate_operation_carbon,
    calculate_transport_carbon,
    solve_green_schedule,
)


class TestCalculateOperationCarbon:
    def test_basic(self):
        carbon = calculate_operation_carbon(60, 10.0, 0.5)
        assert carbon == 5.0

    def test_zero_energy(self):
        carbon = calculate_operation_carbon(60, 0.0, 0.5)
        assert carbon == 0.0

    def test_zero_duration(self):
        carbon = calculate_operation_carbon(0, 10.0, 0.5)
        assert carbon == 0.0

    def test_high_emission(self):
        carbon = calculate_operation_carbon(60, 10.0, 0.9)
        assert carbon == 9.0


class TestCalculateTransportCarbon:
    def test_basic(self):
        carbon = calculate_transport_carbon(100, 50.0, 0.001)
        assert carbon > 0

    def test_with_load_factor(self):
        carbon1 = calculate_transport_carbon(100, 50.0, 0.001, 0.5)
        carbon2 = calculate_transport_carbon(100, 50.0, 0.001, 1.0)
        assert carbon2 > carbon1

    def test_zero_quantity(self):
        carbon = calculate_transport_carbon(0, 50.0, 0.001)
        assert carbon == 0.0


class TestSolveGreenSchedule:
    def test_single_operation(self):
        wcs = [{"id": "wc1", "energy_kwh_per_hour": 10.0, "cost_per_hour": 50.0}]
        ops = [{"id": "op1", "work_center_id": "wc1", "duration_mins": 60}]
        ef = [EmissionFactorData("grid", "global", 0.5)]
        result = solve_green_schedule(wcs, ops, ef, [], [])
        assert result.solver_status in ("OPTIMAL", "FEASIBLE")
        assert len(result.assignments) == 1
        assert result.total_carbon_kg > 0

    def test_two_operations_different_carbon(self):
        wcs = [
            {"id": "wc1", "energy_kwh_per_hour": 10.0, "cost_per_hour": 50.0},
            {"id": "wc2", "energy_kwh_per_hour": 2.0, "cost_per_hour": 80.0},
        ]
        ops = [
            {"id": "op1", "work_center_id": "wc1", "duration_mins": 60},
            {"id": "op2", "work_center_id": "wc2", "duration_mins": 60},
        ]
        ef = [EmissionFactorData("grid", "global", 0.5)]
        result = solve_green_schedule(wcs, ops, ef, [], [])
        assert result.solver_status in ("OPTIMAL", "FEASIBLE")
        assert len(result.assignments) == 2

    def test_carbon_breakdown(self):
        wcs = [{"id": "wc1", "energy_kwh_per_hour": 10.0, "cost_per_hour": 50.0}]
        ops = [{"id": "op1", "work_center_id": "wc1", "duration_mins": 60}]
        ef = [EmissionFactorData("grid", "global", 0.5)]
        result = solve_green_schedule(wcs, ops, ef, [], [])
        assert "wc1" in result.carbon_breakdown

    def test_carbon_per_unit(self):
        wcs = [{"id": "wc1", "energy_kwh_per_hour": 10.0, "cost_per_hour": 50.0}]
        ops = [
            {"id": "op1", "work_center_id": "wc1", "duration_mins": 60},
            {"id": "op2", "work_center_id": "wc1", "duration_mins": 60},
        ]
        ef = [EmissionFactorData("grid", "global", 0.5)]
        result = solve_green_schedule(wcs, ops, ef, [], [])
        assert result.carbon_per_unit > 0

    def test_empty_operations(self):
        wcs = [{"id": "wc1", "energy_kwh_per_hour": 10.0, "cost_per_hour": 50.0}]
        ef = [EmissionFactorData("grid", "global", 0.5)]
        result = solve_green_schedule(wcs, [], ef, [], [])
        assert result.solver_status in ("OPTIMAL", "FEASIBLE")
        assert len(result.assignments) == 0
        assert result.total_carbon_kg == 0

    def test_no_emission_factors_defaults(self):
        wcs = [{"id": "wc1", "energy_kwh_per_hour": 10.0, "cost_per_hour": 50.0}]
        ops = [{"id": "op1", "work_center_id": "wc1", "duration_mins": 60}]
        result = solve_green_schedule(wcs, ops, [], [], [])
        assert result.solver_status in ("OPTIMAL", "FEASIBLE")

    def test_zero_energy_work_center(self):
        wcs = [{"id": "wc1", "energy_kwh_per_hour": 0.0, "cost_per_hour": 50.0}]
        ops = [{"id": "op1", "work_center_id": "wc1", "duration_mins": 60}]
        ef = [EmissionFactorData("grid", "global", 0.5)]
        result = solve_green_schedule(wcs, ops, ef, [], [])
        assert result.total_carbon_kg == 0.0

    def test_beta_zero_minimizes_cost(self):
        wcs = [{"id": "wc1", "energy_kwh_per_hour": 10.0, "cost_per_hour": 50.0}]
        ops = [{"id": "op1", "work_center_id": "wc1", "duration_mins": 60}]
        ef = [EmissionFactorData("grid", "global", 0.5)]
        result = solve_green_schedule(wcs, ops, ef, [], [], beta=0.0)
        assert result.solver_status in ("OPTIMAL", "FEASIBLE")
