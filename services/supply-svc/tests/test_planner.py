from app.core.planner import build_replenishment_plan


def test_replenishment_plan_transfers():
    plants = [{"id": "p1", "name": "East", "code": "E1"}, {"id": "p2", "name": "West", "code": "W1"}]
    routes = [
        {
            "origin_plant_id": "p1",
            "destination_plant_id": "p2",
            "transit_time_hours": 24,
            "cost_per_unit": 1.5,
        }
    ]
    inv = [{"location_id": "p1", "qty_on_hand": 1000}, {"location_id": "p2", "qty_on_hand": 50}]
    plan = build_replenishment_plan(plants, routes, inv)
    assert plan["echelon_count"] == 2
    assert plan["network_inventory_total"] == 1050
