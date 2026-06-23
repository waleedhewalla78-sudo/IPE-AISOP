"""Planner Copilot tools: function definitions and handlers for LLM tool calling.

These tools allow the LLM to query production data and trigger scenario simulations
through a controlled, read-only interface. The LLM CANNOT update or delete live records.
"""

import httpx
from app.config import settings


async def get_order_status(order_id: str, tenant_id: str) -> dict:
    """Get the current status and schedule of a manufacturing order.

    Args:
        order_id: The manufacturing order ID.
        tenant_id: The tenant ID for authorization.

    Returns:
        Dict with MO details including planned dates, status, and feasibility score.
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(
                f"{settings.CAP_SVC_URL}/api/v1/capacity/schedule",
                json={"mo_ids": [order_id]},
                headers={"X-Tenant-ID": tenant_id},
            )
            if resp.status_code == 200:
                data = resp.json()
                assignments = data.get("data", {}).get("schedule", {}).get("assignments", [])
                mo_ops = [a for a in assignments if a.get("mo_id") == order_id]
                if mo_ops:
                    starts = [a["start_minute"] for a in mo_ops]
                    ends = [a["end_minute"] for a in mo_ops]
                    return {
                        "order_id": order_id,
                        "status": "scheduled",
                        "planned_start_minute": min(starts),
                        "planned_end_minute": max(ends),
                        "total_operations": len(mo_ops),
                        "on_time": all(a.get("on_time", False) for a in mo_ops),
                    }
                return {"order_id": order_id, "status": "not_scheduled", "message": "MO not found in current schedule"}
            return {"order_id": order_id, "status": "error", "message": f"cap-svc returned {resp.status_code}"}
    except Exception as e:
        return {"order_id": order_id, "status": "error", "message": str(e)}


async def get_resource_utilization(resource_id: str, tenant_id: str) -> dict:
    """Get capacity utilization for a work center.

    Args:
        resource_id: The work center ID.
        tenant_id: The tenant ID for authorization.

    Returns:
        Dict with utilization metrics including load percentage and assigned operations.
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(
                f"{settings.CAP_SVC_URL}/api/v1/capacity/schedule",
                json={},
                headers={"X-Tenant-ID": tenant_id},
            )
            if resp.status_code == 200:
                data = resp.json()
                assignments = data.get("data", {}).get("schedule", {}).get("assignments", [])
                wc_ops = [a for a in assignments if a.get("work_center_id") == resource_id]
                total_duration = sum(a.get("duration", 0) for a in wc_ops)
                horizon = 168 * 60
                utilization_pct = round(total_duration / horizon * 100, 1) if horizon > 0 else 0
                return {
                    "resource_id": resource_id,
                    "utilization_pct": utilization_pct,
                    "assigned_operations": len(wc_ops),
                    "total_scheduled_minutes": total_duration,
                }
            return {"resource_id": resource_id, "status": "error", "message": f"cap-svc returned {resp.status_code}"}
    except Exception as e:
        return {"resource_id": resource_id, "status": "error", "message": str(e)}


async def simulate_disruption(resource_id: str, downtime_hours: int, tenant_id: str) -> dict:
    """Simulate a machine breakdown and return impact on order delivery dates.

    Uses the Sprint 6 scenario sandbox (clone -> inject disruption -> solve -> diff).
    The LLM CANNOT directly modify live UDM records.

    Args:
        resource_id: The work center to simulate downtime for.
        downtime_hours: Hours of downtime to simulate.
        tenant_id: The tenant ID for authorization.

    Returns:
        Dict with scenario results including delayed orders and impact summary.
    """
    try:
        headers = {"X-Tenant-ID": tenant_id}
        async with httpx.AsyncClient(timeout=30.0) as client:
            clone_resp = await client.post(
                f"{settings.CAP_SVC_URL}/api/v1/scenarios/clone",
                json={"mo_ids": [], "name": f"copilot_disruption_{resource_id}", "description": f"Simulated {downtime_hours}h downtime"},
                headers=headers,
            )
            if clone_resp.status_code != 200:
                return {"status": "error", "message": f"Failed to clone scenario: {clone_resp.status_code}"}
            scenario_id = clone_resp.json().get("data", {}).get("scenario_id")

            disruption_resp = await client.post(
                f"{settings.CAP_SVC_URL}/api/v1/scenarios/{scenario_id}/disruption",
                json={"resource_id": resource_id, "capacity_multiplier": 0.0, "delay_days": downtime_hours // 24},
                headers=headers,
            )
            if disruption_resp.status_code != 200:
                return {"status": "error", "message": f"Failed to inject disruption: {disruption_resp.status_code}"}

            solve_resp = await client.post(
                f"{settings.CAP_SVC_URL}/api/v1/scenarios/{scenario_id}/solve",
                json={},
                headers=headers,
            )
            if solve_resp.status_code != 200:
                return {"status": "error", "message": f"Failed to solve scenario: {solve_resp.status_code}"}

            diff_resp = await client.get(
                f"{settings.CAP_SVC_URL}/api/v1/scenarios/{scenario_id}/diff",
                headers=headers,
            )
            if diff_resp.status_code == 200:
                diff_data = diff_resp.json().get("data", {})
                return {
                    "scenario_id": scenario_id,
                    "resource_id": resource_id,
                    "downtime_hours": downtime_hours,
                    "impact": diff_data.get("impact", {}),
                    "baseline": diff_data.get("baseline", {}),
                    "scenario": diff_data.get("scenario", {}),
                }

            return {
                "scenario_id": scenario_id,
                "resource_id": resource_id,
                "downtime_hours": downtime_hours,
                "status": "solved_but_diff_failed",
            }
    except Exception as e:
        return {"status": "error", "message": str(e)}


TOOL_DEFINITIONS = [
    {
        "name": "get_order_status",
        "description": "Get the current status, planned schedule, and on-time performance of a manufacturing order.",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string", "description": "The manufacturing order ID"},
            },
            "required": ["order_id"],
        },
    },
    {
        "name": "get_resource_utilization",
        "description": "Get capacity utilization percentage and load for a work center or machine.",
        "input_schema": {
            "type": "object",
            "properties": {
                "resource_id": {"type": "string", "description": "The work center or machine ID"},
            },
            "required": ["resource_id"],
        },
    },
    {
        "name": "simulate_disruption",
        "description": "Simulate a machine breakdown or capacity loss and return the impact on scheduled orders. Uses the isolated scenario sandbox - no live data is modified.",
        "input_schema": {
            "type": "object",
            "properties": {
                "resource_id": {"type": "string", "description": "The work center or machine to simulate downtime for"},
                "downtime_hours": {"type": "integer", "description": "Number of hours of downtime to simulate"},
            },
            "required": ["resource_id", "downtime_hours"],
        },
    },
]

TOOL_HANDLERS = {
    "get_order_status": get_order_status,
    "get_resource_utilization": get_resource_utilization,
    "simulate_disruption": simulate_disruption,
}
