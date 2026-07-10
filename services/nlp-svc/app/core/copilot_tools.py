"""Planner Copilot tools: function definitions and handlers for LLM tool calling.

These tools allow the LLM to query production data and trigger scenario simulations
through a controlled, read-only interface. The LLM CANNOT update or delete live records.
"""

import httpx
from app.config import settings


def _tenant_headers(tenant_id: str) -> dict[str, str]:
    return {"X-Tenant-ID": tenant_id}


def _unwrap_api_payload(body: dict) -> dict | list:
    data = body.get("data")
    if data is not None:
        return data
    return body


async def _planning_get(
    url: str,
    tenant_id: str,
    *,
    params: dict | None = None,
    timeout: float = 10.0,
) -> dict:
    """GET a planning service endpoint with tenant header."""
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.get(url, params=params or {}, headers=_tenant_headers(tenant_id))
            if resp.status_code == 200:
                payload = _unwrap_api_payload(resp.json())
                if isinstance(payload, dict):
                    return {"status": "ok", **payload}
                return {"status": "ok", "items": payload}
            return {"status": "error", "message": f"HTTP {resp.status_code} from {url}"}
    except Exception as exc:
        return {"status": "error", "message": str(exc), "url": url}


async def get_mo_status(mo_id: str | None, tenant_id: str) -> dict:
    """Fetch manufacturing order status from the control tower dashboard."""
    params: dict[str, str] = {}
    if mo_id:
        params["mo_id"] = mo_id
    return await _planning_get(
        f"{settings.DPE_SVC_URL}/api/v1/dashboard/mos",
        tenant_id,
        params=params or None,
    )


async def get_feasibility_queue(tenant_id: str) -> dict:
    """Fetch MOs in the feasibility risk queue (lowest scores first)."""
    return await _planning_get(
        f"{settings.FEA_SVC_URL}/api/v1/feasibility/queue",
        tenant_id,
    )


async def get_schedule(tenant_id: str) -> dict:
    """Fetch the active production schedule."""
    return await _planning_get(
        f"{settings.CAP_SVC_URL}/api/v1/capacity/schedule/active",
        tenant_id,
        timeout=20.0,
    )


async def get_otd_metrics(tenant_id: str) -> dict:
    """Fetch on-time delivery analytics for the tenant."""
    primary = await _planning_get(
        f"{settings.DPE_SVC_URL}/api/v1/dashboard/analytics",
        tenant_id,
    )
    if primary.get("status") == "ok":
        return primary
    fallback = await _planning_get(
        f"{settings.DPE_SVC_URL}/api/v1/analytics/otd-baseline",
        tenant_id,
    )
    if fallback.get("status") == "ok":
        return fallback
    return primary


async def get_material_availability(
    product_id: str,
    quantity: float,
    required_date: str,
    tenant_id: str,
) -> dict:
    """Check rule-based material availability (ATP) for a product."""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"{settings.MAT_SVC_URL}/api/v1/material/check-availability",
                json={
                    "product_id": product_id,
                    "quantity": quantity,
                    "required_date": required_date,
                },
                headers=_tenant_headers(tenant_id),
            )
            if resp.status_code == 200:
                payload = _unwrap_api_payload(resp.json())
                if isinstance(payload, dict):
                    return {"status": "ok", **payload}
                return {"status": "ok", "result": payload}
            return {
                "status": "error",
                "message": f"mat-svc returned {resp.status_code}",
            }
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


async def get_sync_status(tenant_id: str) -> dict:
    """Fetch ERP sync status from the connector service."""
    return await _planning_get(
        f"{settings.CONNECTOR_SVC_URL}/api/v1/sync/status",
        tenant_id,
    )


async def get_resolution_scenarios(mo_id: str, tenant_id: str) -> dict:
    """Fetch proposed resolution scenarios for a manufacturing order."""
    primary = await _planning_get(
        f"{settings.DPE_SVC_URL}/api/v1/resolution/scenarios/{mo_id}",
        tenant_id,
    )
    if primary.get("status") == "ok":
        return primary
    return await _planning_get(
        f"{settings.RES_SVC_URL}/api/v1/resolution/scenarios",
        tenant_id,
        params={"mo_id": mo_id},
    )


async def get_forecast_accuracy(tenant_id: str, lag: int = 3) -> dict:
    """Current forecast accuracy (MAPE) across products."""
    return await _planning_get(
        f"{settings.DEMAND_SVC_URL}/api/v1/demand/error/mape",
        tenant_id,
        params={"lag": lag},
    )


async def get_forecast_bias(tenant_id: str, lag: int = 3) -> dict:
    """Forecast bias — systematic over/under forecasting."""
    return await _planning_get(
        f"{settings.DEMAND_SVC_URL}/api/v1/demand/error/bias",
        tenant_id,
        params={"lag": lag},
    )


async def get_product_segments(tenant_id: str) -> dict:
    """ABC/XYZ product segmentation matrix."""
    return await _planning_get(
        f"{settings.MAT_SVC_URL}/api/v1/material/segmentation/summary",
        tenant_id,
    )


async def get_safety_stock_gaps(tenant_id: str) -> dict:
    """Safety stock gaps — over/under stocked products."""
    return await _planning_get(
        f"{settings.MAT_SVC_URL}/api/v1/material/safety-stock/summary",
        tenant_id,
    )


async def get_capacity_alerts(tenant_id: str) -> dict:
    """Overloaded work centers above utilisation threshold."""
    return await _planning_get(
        f"{settings.CAP_SVC_URL}/api/v1/capacity/utilisation/alerts",
        tenant_id,
    )


async def get_capacity_ranking(tenant_id: str, top_n: int = 5) -> dict:
    """Most utilised work centers."""
    return await _planning_get(
        f"{settings.CAP_SVC_URL}/api/v1/capacity/utilisation/ranking",
        tenant_id,
        params={"top_n": top_n},
    )


async def get_sop_cycle_status(tenant_id: str) -> dict:
    """Current S&OP cycle stage and deadlines."""
    return await _planning_get(
        f"{settings.SOP_SVC_URL}/api/v1/sop/cycle",
        tenant_id,
    )


async def get_consensus_vs_plan(tenant_id: str) -> dict:
    """Consensus demand vs plan / reconciliation dashboard."""
    return await _planning_get(
        f"{settings.SOP_SVC_URL}/api/v1/sop/reconciliation/dashboard",
        tenant_id,
    )


async def compare_sop_versions(tenant_id: str, a: str | None = None, b: str | None = None) -> dict:
    """Side-by-side S&OP version comparison."""
    params: dict[str, str] = {}
    if a:
        params["a"] = a
    if b:
        params["b"] = b
    return await _planning_get(
        f"{settings.SOP_SVC_URL}/api/v1/sop/version/compare",
        tenant_id,
        params=params or None,
    )


async def analyze_quality_patterns(
    tenant_id: str,
    lookback_days: int = 30,
) -> dict:
    """Aggregate quality defect patterns from quality-svc / del-svc."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{settings.CAP_SVC_URL}/api/v1/analytics/bottlenecks",
                headers={"X-Tenant-ID": tenant_id},
            )
            bottleneck_data = resp.json().get("data", {}) if resp.status_code == 200 else {}

            util_resp = await client.get(
                f"{settings.CAP_SVC_URL}/api/v1/analytics/utilisation",
                headers={"X-Tenant-ID": tenant_id},
            )
            util_data = util_resp.json().get("data", {}) if util_resp.status_code == 200 else {}

        patterns = []
        for wc in bottleneck_data.get("top_bottlenecks", [])[:3]:
            patterns.append(
                {
                    "pattern": "capacity_stress",
                    "work_center": wc.get("work_center_name"),
                    "utilization_pct": wc.get("utilization_pct"),
                    "severity": wc.get("severity"),
                }
            )

        return {
            "lookback_days": lookback_days,
            "pattern_count": len(patterns),
            "patterns": patterns,
            "average_utilization_pct": util_data.get("average_utilization_pct"),
            "recommendation": (
                "Review quality holds on overloaded work centers"
                if patterns
                else "No significant quality-capacity correlation detected"
            ),
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


async def get_supplier_risk(tenant_id: str) -> dict:
    """Fetch supplier risk scores from mat-svc."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{settings.MAT_SVC_URL}/api/v1/supply-chain/supplier-risk",
                headers={"X-Tenant-ID": tenant_id},
            )
            if resp.status_code == 200:
                return resp.json().get("data", {})
            return {"status": "error", "message": f"mat-svc returned {resp.status_code}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


async def get_inventory_abc(tenant_id: str) -> dict:
    """Fetch ABC inventory classification from mat-svc."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{settings.MAT_SVC_URL}/api/v1/supply-chain/inventory-abc",
                headers={"X-Tenant-ID": tenant_id},
            )
            if resp.status_code == 200:
                return resp.json().get("data", {})
            return {"status": "error", "message": f"mat-svc returned {resp.status_code}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


async def get_slow_moving_inventory(tenant_id: str, stale_days: int = 90) -> dict:
    """Fetch slow-moving inventory from mat-svc."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{settings.MAT_SVC_URL}/api/v1/supply-chain/slow-moving",
                params={"stale_days": stale_days},
                headers={"X-Tenant-ID": tenant_id},
            )
            if resp.status_code == 200:
                return resp.json().get("data", {})
            return {"status": "error", "message": f"mat-svc returned {resp.status_code}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


async def get_reorder_suggestions(tenant_id: str) -> dict:
    """Fetch reorder suggestions from mat-svc."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{settings.MAT_SVC_URL}/api/v1/supply-chain/reorder-suggestions",
                headers={"X-Tenant-ID": tenant_id},
            )
            if resp.status_code == 200:
                return resp.json().get("data", {})
            return {"status": "error", "message": f"mat-svc returned {resp.status_code}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


async def get_war_room_recovery(
    disruption_id: str | None,
    tenant_id: str,
) -> dict:
    """Fetch top recovery scenarios from War Room for a disruption event."""
    try:
        params = {}
        if disruption_id:
            params["disruption_id"] = disruption_id
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{settings.ALERT_SVC_URL}/api/v1/war-room/recovery-plan",
                params=params,
                headers={"X-Tenant-ID": tenant_id},
            )
            if resp.status_code == 200:
                data = resp.json().get("data") or {}
                options = data.get("recovery_options") or []
                cited = [
                    {
                        "rank": opt.get("rank"),
                        "scenario_id": opt.get("scenario_id"),
                        "business_score_usd": opt.get("business_score_usd"),
                        "activity_cost_usd": opt.get("activity_cost_usd"),
                        "summary": opt.get("summary"),
                    }
                    for opt in options
                ]
                return {
                    "disruption_id": data.get("disruption_id"),
                    "impacted_mo_count": data.get("impacted_mo_count"),
                    "recovery_options": cited,
                    "scenario_ids": [opt.get("scenario_id") for opt in cited if opt.get("scenario_id")],
                }
            return {"status": "error", "message": f"alert-svc returned {resp.status_code}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


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
    {
        "name": "analyze_quality_patterns",
        "description": "Analyze quality defect patterns correlated with capacity bottlenecks and utilization stress.",
        "input_schema": {
            "type": "object",
            "properties": {
                "lookback_days": {
                    "type": "integer",
                    "description": "Days of history to analyze (default 30)",
                },
            },
            "required": [],
        },
    },
    {
        "name": "get_supplier_risk",
        "description": "Get supplier reliability scores and risk tiers for the tenant supply base.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_inventory_abc",
        "description": "Get ABC inventory classification by on-hand quantity share.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_slow_moving_inventory",
        "description": "List slow-moving inventory SKUs with no recent receipts.",
        "input_schema": {
            "type": "object",
            "properties": {
                "stale_days": {"type": "integer", "description": "Days without movement (default 90)"},
            },
            "required": [],
        },
    },
    {
        "name": "get_reorder_suggestions",
        "description": "Get purchase reorder suggestions for purchased materials below reorder point.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_war_room_recovery",
        "description": "Get top 3 War Room recovery scenarios for a disruption, including scenario_id citations for planner approval.",
        "input_schema": {
            "type": "object",
            "properties": {
                "disruption_id": {
                    "type": "string",
                    "description": "Disruption event UUID; omit to use latest Tier-1 event",
                },
            },
            "required": [],
        },
    },
    {
        "name": "get_mo_status",
        "description": "Get manufacturing order status, feasibility score, and primary constraint from live planning data.",
        "input_schema": {
            "type": "object",
            "properties": {
                "mo_id": {
                    "type": "string",
                    "description": "Manufacturing order ID or ERP reference (e.g. MO-ST-001); omit for all active MOs",
                },
            },
            "required": [],
        },
    },
    {
        "name": "get_feasibility_queue",
        "description": "List manufacturing orders in the feasibility risk queue sorted by lowest score.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_schedule",
        "description": "Get the active finite-capacity production schedule.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_otd_metrics",
        "description": "Get on-time delivery (OTD) metrics and analytics for the tenant.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_material_availability",
        "description": "Check material availability (ATP) for a product on a required date.",
        "input_schema": {
            "type": "object",
            "properties": {
                "product_id": {"type": "string", "description": "Product UUID"},
                "quantity": {"type": "number", "description": "Required quantity"},
                "required_date": {"type": "string", "description": "ISO date (YYYY-MM-DD)"},
            },
            "required": ["product_id", "quantity", "required_date"],
        },
    },
    {
        "name": "get_sync_status",
        "description": "Get ERP/Odoo sync status including last run and data-quality monitor state.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_resolution_scenarios",
        "description": "Get proposed resolution scenarios for a manufacturing order (read-only; planner must approve).",
        "input_schema": {
            "type": "object",
            "properties": {
                "mo_id": {"type": "string", "description": "Manufacturing order UUID"},
            },
            "required": ["mo_id"],
        },
    },
    {
        "name": "get_forecast_accuracy",
        "description": "Get forecast accuracy (MAPE/bias) across products for planning quality review.",
        "input_schema": {
            "type": "object",
            "properties": {
                "lag": {"type": "integer", "description": "Lag periods for error calculation (default 3)"},
            },
            "required": [],
        },
    },
    {
        "name": "get_forecast_bias",
        "description": "Get forecast bias — whether forecasts are systematically high or low.",
        "input_schema": {
            "type": "object",
            "properties": {
                "lag": {"type": "integer", "description": "Lag periods (default 3)"},
            },
            "required": [],
        },
    },
    {
        "name": "get_product_segments",
        "description": "Get ABC/XYZ product segmentation matrix with counts and revenue share.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_safety_stock_gaps",
        "description": "Get safety stock gaps: total value, over-stocked and under-stocked products.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_capacity_alerts",
        "description": "Get overloaded work centers at or above capacity utilisation threshold.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_capacity_ranking",
        "description": "Get top most utilised work centers.",
        "input_schema": {
            "type": "object",
            "properties": {
                "top_n": {"type": "integer", "description": "Number of work centers (default 5)"},
            },
            "required": [],
        },
    },
    {
        "name": "get_sop_cycle_status",
        "description": "Get current S&OP cycle stage, status, and deadlines.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_consensus_vs_plan",
        "description": "Get consensus demand vs plan reconciliation dashboard (revenue gap, lost sales).",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "compare_sop_versions",
        "description": "Compare two S&OP versions side by side (baseline vs upside/downside).",
        "input_schema": {
            "type": "object",
            "properties": {
                "a": {"type": "string", "description": "First version id"},
                "b": {"type": "string", "description": "Second version id"},
            },
            "required": [],
        },
    },
]

TOOL_HANDLERS = {
    "get_order_status": get_order_status,
    "get_resource_utilization": get_resource_utilization,
    "simulate_disruption": simulate_disruption,
    "get_war_room_recovery": get_war_room_recovery,
    "analyze_quality_patterns": analyze_quality_patterns,
    "get_supplier_risk": get_supplier_risk,
    "get_inventory_abc": get_inventory_abc,
    "get_slow_moving_inventory": get_slow_moving_inventory,
    "get_reorder_suggestions": get_reorder_suggestions,
    "get_mo_status": get_mo_status,
    "get_feasibility_queue": get_feasibility_queue,
    "get_schedule": get_schedule,
    "get_otd_metrics": get_otd_metrics,
    "get_material_availability": get_material_availability,
    "get_sync_status": get_sync_status,
    "get_resolution_scenarios": get_resolution_scenarios,
    "get_forecast_accuracy": get_forecast_accuracy,
    "get_forecast_bias": get_forecast_bias,
    "get_product_segments": get_product_segments,
    "get_safety_stock_gaps": get_safety_stock_gaps,
    "get_capacity_alerts": get_capacity_alerts,
    "get_capacity_ranking": get_capacity_ranking,
    "get_sop_cycle_status": get_sop_cycle_status,
    "get_consensus_vs_plan": get_consensus_vs_plan,
    "compare_sop_versions": compare_sop_versions,
}
