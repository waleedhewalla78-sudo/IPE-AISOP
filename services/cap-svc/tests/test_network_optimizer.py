import pytest
from app.core.network_optimizer import (
    PlantData,
    TransferRouteData,
    FleetData,
    NetworkDemand,
    solve_network_optimization,
    build_distance_penalty,
)


class TestPlantData:
    def test_basic_creation(self):
        plant = PlantData(
            plant_id="p1",
            name="Plant A",
            capacity_hours=8.0,
            cost_per_hour=50.0,
            energy_kwh_per_hour=10.0,
        )
        assert plant.plant_id == "p1"
        assert plant.capabilities == []

    def test_with_capabilities(self):
        plant = PlantData(
            plant_id="p1",
            name="Plant A",
            capacity_hours=8.0,
            cost_per_hour=50.0,
            energy_kwh_per_hour=10.0,
            capabilities=["assembly", "painting"],
        )
        assert len(plant.capabilities) == 2


class TestTransferRouteData:
    def test_basic_creation(self):
        route = TransferRouteData(
            route_id="r1",
            origin_plant_id="p1",
            destination_plant_id="p2",
            transit_time_hours=24.0,
            cost_per_unit=5.0,
            capacity_units=1000,
            reliability_score=0.95,
        )
        assert route.origin_plant_id == "p1"
        assert route.reliability_score == 0.95


class TestFleetData:
    def test_basic_creation(self):
        fleet = FleetData(
            fleet_id="f1",
            route_id="r1",
            available_units=3,
            max_trips_per_day=5,
            cost_per_trip=500.0,
        )
        assert fleet.available_units == 3


class TestNetworkDemand:
    def test_basic_creation(self):
        demand = NetworkDemand(
            demand_id="d1",
            product_id="prod1",
            quantity=100,
            required_date="2026-07-01",
            priority_score=0.8,
            penalty_cost=200.0,
        )
        assert demand.capable_plants == []

    def test_with_capable_plants(self):
        demand = NetworkDemand(
            demand_id="d1",
            product_id="prod1",
            quantity=100,
            required_date="2026-07-01",
            priority_score=0.8,
            penalty_cost=200.0,
            capable_plants=["p1", "p2"],
        )
        assert len(demand.capable_plants) == 2


class TestDistancePenalty:
    def test_none_coordinates(self):
        penalty = build_distance_penalty(None, None, None, None)
        assert penalty == 1.0

    def test_same_location(self):
        penalty = build_distance_penalty(40.0, -74.0, 40.0, -74.0)
        assert penalty == 1.0

    def test_different_locations(self):
        penalty = build_distance_penalty(40.0, -74.0, 34.0, -118.0)
        assert penalty > 1.0


class TestSolveNetworkOptimization:
    def test_single_plant_single_demand(self):
        plants = [
            PlantData("p1", "Plant A", 8.0, 50.0, 10.0),
        ]
        demands = [
            NetworkDemand("d1", "prod1", 100, "2026-07-01", 0.8, 200.0, ["p1"]),
        ]
        result = solve_network_optimization(
            plants=plants, routes=[], fleets=[], demands=demands,
            work_centers=[], operations=[], alpha=0.5,
        )
        assert result.solver_status in ("OPTIMAL", "FEASIBLE")
        assert len(result.assignments) == 1
        assert result.assignments[0]["plant_id"] == "p1"

    def test_two_plants_cheapest_wins(self):
        plants = [
            PlantData("p1", "Plant A", 8.0, 30.0, 10.0),
            PlantData("p2", "Plant B", 8.0, 80.0, 10.0),
        ]
        demands = [
            NetworkDemand("d1", "prod1", 100, "2026-07-01", 0.8, 200.0, ["p1", "p2"]),
        ]
        result = solve_network_optimization(
            plants=plants, routes=[], fleets=[], demands=demands,
            work_centers=[], operations=[], alpha=0.5,
        )
        assert result.solver_status in ("OPTIMAL", "FEASIBLE")
        assert len(result.assignments) == 1
        assert result.assignments[0]["plant_id"] == "p1"

    def test_transfer_when_local_expensive(self):
        plants = [
            PlantData("p1", "Plant A", 8.0, 100.0, 10.0),
            PlantData("p2", "Plant B", 8.0, 20.0, 10.0),
        ]
        routes = [
            TransferRouteData("r1", "p2", "p1", 24.0, 1.0, 1000, 0.95),
        ]
        fleets = [
            FleetData("f1", "r1", 3, 5, 100.0),
        ]
        demands = [
            NetworkDemand("d1", "prod1", 100, "2026-07-01", 0.8, 200.0, ["p1", "p2"]),
        ]
        result = solve_network_optimization(
            plants=plants, routes=routes, fleets=fleets, demands=demands,
            work_centers=[], operations=[], alpha=0.5,
        )
        assert result.solver_status in ("OPTIMAL", "FEASIBLE")
        assert len(result.assignments) == 1
        assert result.assignments[0]["plant_id"] == "p2"

    def test_no_capable_plants_unsatisfied(self):
        plants = [
            PlantData("p1", "Plant A", 8.0, 50.0, 10.0, capabilities=["welding"]),
        ]
        demands = [
            NetworkDemand("d1", "prod1", 100, "2026-07-01", 0.8, 200.0, []),
        ]
        result = solve_network_optimization(
            plants=plants, routes=[], fleets=[], demands=demands,
            work_centers=[], operations=[], alpha=0.5,
        )
        assert result.solver_status in ("OPTIMAL", "FEASIBLE", "INFEASIBLE")
        assert len(result.unsatisfied_demands) == 1

    def test_multiple_demands(self):
        plants = [
            PlantData("p1", "Plant A", 8.0, 50.0, 10.0),
            PlantData("p2", "Plant B", 8.0, 60.0, 10.0),
        ]
        demands = [
            NetworkDemand("d1", "prod1", 100, "2026-07-01", 0.8, 200.0, ["p1", "p2"]),
            NetworkDemand("d2", "prod2", 200, "2026-07-02", 0.6, 300.0, ["p1", "p2"]),
        ]
        result = solve_network_optimization(
            plants=plants, routes=[], fleets=[], demands=demands,
            work_centers=[], operations=[], alpha=0.5,
        )
        assert result.solver_status in ("OPTIMAL", "FEASIBLE")
        assert len(result.assignments) == 2

    def test_alpha_zero_minimizes_cost(self):
        plants = [
            PlantData("p1", "Plant A", 8.0, 10.0, 10.0),
            PlantData("p2", "Plant B", 8.0, 100.0, 10.0),
        ]
        demands = [
            NetworkDemand("d1", "prod1", 100, "2026-07-01", 0.8, 50.0, ["p1", "p2"]),
        ]
        result = solve_network_optimization(
            plants=plants, routes=[], fleets=[], demands=demands,
            work_centers=[], operations=[], alpha=0.1,
        )
        assert result.solver_status in ("OPTIMAL", "FEASIBLE")
        assert result.assignments[0]["plant_id"] == "p1"

    def test_empty_demands(self):
        plants = [
            PlantData("p1", "Plant A", 8.0, 50.0, 10.0),
        ]
        result = solve_network_optimization(
            plants=plants, routes=[], fleets=[], demands=[],
            work_centers=[], operations=[], alpha=0.5,
        )
        assert result.solver_status in ("OPTIMAL", "FEASIBLE")
        assert len(result.assignments) == 0

    def test_total_costs_computed(self):
        plants = [
            PlantData("p1", "Plant A", 8.0, 50.0, 10.0),
        ]
        demands = [
            NetworkDemand("d1", "prod1", 100, "2026-07-01", 0.8, 200.0, ["p1"]),
        ]
        result = solve_network_optimization(
            plants=plants, routes=[], fleets=[], demands=demands,
            work_centers=[], operations=[], alpha=0.5,
        )
        assert result.total_make_cost >= 0
        assert result.total_transfer_cost >= 0
        assert result.total_penalty >= 0
