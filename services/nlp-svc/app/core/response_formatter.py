"""Format structured copilot data when LLM providers are unavailable."""

from __future__ import annotations

import json
from typing import Any


def is_llm_error(response: str) -> bool:
    lowered = response.lower()
    return lowered.startswith("llm error:") or "not configured" in lowered or "unavailable" in lowered


def format_structured_response(intent: str, structured_data: Any) -> str | None:
    """Build a human-readable answer from fetched system data."""
    if isinstance(structured_data, str):
        try:
            structured_data = json.loads(structured_data)
        except json.JSONDecodeError:
            if structured_data and not structured_data.startswith("Could not fetch"):
                return structured_data
            return None

    if not isinstance(structured_data, dict):
        return None

    if structured_data.get("error"):
        return f"Could not retrieve data: {structured_data['error']}"

    if intent == "material_status":
        return _format_inventory(structured_data)
    if intent == "demand_query":
        return _format_demands(structured_data)
    if intent == "capacity_status":
        return _format_capacity(structured_data)
    if intent == "delay_analysis":
        return _format_delays(structured_data)
    if intent == "feasibility_check":
        return _format_feasibility(structured_data)
    if intent == "resolution_help":
        return _format_resolution(structured_data)

    summary = structured_data.get("summary")
    return str(summary) if summary else None


def _format_inventory(data: dict) -> str | None:
    items = data.get("items") or []
    if not items:
        return "No inventory records found for finished goods in the current tenant."

    lines = [f"Current finished goods (FG) stock — {len(items)} item(s):"]
    for item in items:
        name = item.get("name", "Unknown")
        ref = item.get("internal_ref") or item.get("erp_source_id") or "—"
        uom = item.get("uom") or "unit"
        on_hand = item.get("qty_on_hand", 0)
        reserved = item.get("qty_reserved", 0)
        available = item.get("qty_available", on_hand)
        lines.append(
            f"• {name} ({ref}): {available} {uom} available "
            f"({on_hand} on hand, {reserved} reserved)"
        )
    return "\n".join(lines)


def _format_demands(data: dict) -> str | None:
    items = data.get("items") or data.get("demands") or []
    if not items:
        return "No open demand lines found."

    lines = [f"Open demand — {len(items)} line(s):"]
    for item in items[:10]:
        product = item.get("product_name") or item.get("product") or "Product"
        qty = item.get("quantity", "?")
        due = item.get("required_date") or item.get("due_date") or "—"
        lines.append(f"• {product}: qty {qty}, due {due}")
    return "\n".join(lines)


def _format_capacity(data: dict) -> str | None:
    bottlenecks = data.get("bottlenecks") or []
    utilization = data.get("utilization") or []
    if bottlenecks:
        lines = [f"Capacity bottlenecks — {len(bottlenecks)} work center(s):"]
        for b in bottlenecks[:5]:
            wc = b.get("work_center") or b.get("name") or "Work center"
            util = b.get("utilization_pct") or b.get("load_pct") or "?"
            lines.append(f"• {wc}: {util}% utilization")
        return "\n".join(lines)
    if utilization:
        lines = ["Work center utilization:"]
        for row in utilization[:5]:
            lines.append(f"• {row.get('work_center', 'WC')}: {row.get('utilization_pct', '?')}%")
        return "\n".join(lines)
    total_ops = data.get("total_operations")
    if total_ops is not None:
        return f"Schedule loaded with {total_ops} operation(s). Use Schedule view for Gantt details."
    return None


def _format_delays(data: dict) -> str | None:
    alerts = data.get("alerts") or []
    if not alerts:
        return "No active delay events recorded."

    lines = [f"Active delays — {len(alerts)} event(s):"]
    for alert in alerts[:8]:
        mo = alert.get("mo_ref") or alert.get("mo_id") or "MO"
        cause = alert.get("cause") or alert.get("cause_category") or "unknown"
        mins = alert.get("delay_minutes", 0)
        lines.append(f"• {mo}: {cause} ({mins} min impact)")
    return "\n".join(lines)


def _format_feasibility(data: dict) -> str | None:
    items = data.get("items") or []
    if not items:
        return "No manufacturing orders with feasibility scores."

    at_risk = [i for i in items if (i.get("feasibility_score") or 100) < 70]
    lines = [f"Feasibility queue — {len(items)} MO(s), {len(at_risk)} at risk (<70%):"]
    for item in sorted(items, key=lambda x: x.get("feasibility_score") or 0)[:8]:
        mo = item.get("erp_mo_id") or item.get("mo_id") or "MO"
        score = item.get("feasibility_score", "?")
        constraint = item.get("primary_constraint") or "none"
        lines.append(f"• {mo}: score {score}, constraint {constraint}")
    return "\n".join(lines)


def _format_resolution(data: dict) -> str | None:
    scenarios = data.get("scenarios") or []
    if not scenarios:
        return "No resolution scenarios available. Select an at-risk MO in Resolution Center."

    lines = [f"Resolution scenarios — showing top {min(5, len(scenarios))}:"]
    for s in scenarios[:5]:
        strategy = s.get("strategy") or "strategy"
        mo = s.get("mo_id") or "MO"
        status = s.get("status") or "proposed"
        cost = s.get("cost_impact")
        cost_txt = f", cost ${cost:,.0f}" if cost else ""
        lines.append(f"• {strategy} for {mo} ({status}{cost_txt})")
    return "\n".join(lines)
