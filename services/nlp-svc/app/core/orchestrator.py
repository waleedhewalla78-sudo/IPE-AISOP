"""Query routing orchestrator with intent classification and service aggregation."""

import json

import httpx

from app.config import settings
from app.core.llm_client import query_llm

_INTENTS = [
    "demand_query",
    "material_status",
    "capacity_status",
    "delay_analysis",
    "feasibility_check",
    "resolution_help",
    "general",
]

_INTENT_PROMPT = (
    "You are an intent classifier for a manufacturing orchestration system. "
    f"Classify the following user query into exactly one intent: {', '.join(_INTENTS)}.\n"
    "Reply with only the intent name.\n"
)

_SERVICE_URLS: dict[str, str] = {
    "dpe": settings.DPE_SVC_URL,
    "mat": settings.MAT_SVC_URL,
    "cap": settings.CAP_SVC_URL,
}


async def _classify_intent(query: str) -> str:
    llm_response = await query_llm(_INTENT_PROMPT + f"Query: {query}")
    for intent in _INTENTS:
        if intent in llm_response.lower():
            return intent
    return "general"


async def _fetch_demand_data(_query: str = "") -> str:
    try:
        async with httpx.AsyncClient(timeout=10) as cli:
            resp = await cli.get(f"{_SERVICE_URLS['dpe']}/api/v1/demand/queue")
            if resp.is_success:
                data = resp.json()
                items = data.get("data", {}).get("items", [])
                return f"Demand queue: {len(items)} orders. Latest: {json.dumps(items[:3])}"
            return f"Demand query returned {resp.status_code}"
    except Exception as exc:
        return f"Could not fetch demand data: {exc}"


async def _fetch_material_status(query: str) -> str:
    try:
        async with httpx.AsyncClient(timeout=10) as cli:
            resp = await cli.post(
                f"{_SERVICE_URLS['mat']}/api/v1/material/check-availability-rule",
                json={"query": query},
            )
            if resp.is_success:
                data = resp.json()
                return f"Material availability: {json.dumps(data)}"
            return f"Material check returned {resp.status_code}"
    except Exception as exc:
        return f"Could not fetch material data: {exc}"


async def _fetch_capacity_data(_query: str = "") -> str:
    try:
        async with httpx.AsyncClient(timeout=10) as cli:
            resp = await cli.get(f"{_SERVICE_URLS['cap']}/api/v1/capacity/schedule")
            if resp.is_success:
                data = resp.json()
                bottlenecks = data.get("bottlenecks", [])
                return (
                    f"Capacity: {len(bottlenecks)} bottleneck(s). "
                    f"Details: {json.dumps(bottlenecks[:3])}"
                )
            return f"Capacity query returned {resp.status_code}"
    except Exception as exc:
        return f"Could not fetch capacity data: {exc}"


async def _fetch_delay_analysis(_query: str = "") -> str:
    return (
        "Delay analysis requires a specific MO or date range"
        " — ask the user to provide more details."
    )


async def _fetch_feasibility_data(_query: str = "") -> str:
    return "Feasibility scoring requires a specific MO — ask the user for the MO ID."


async def _fetch_resolution_help(_query: str = "") -> str:
    return "Resolution strategies are available per MO. Ask the user which MO they need help with."


_INTENT_HANDLERS: dict[str, tuple[str, str]] = {
    "demand_query": ("Demand Planning & Order Status", "demand planning and order status"),
    "material_status": (
        "Inventory & Material Availability",
        "inventory levels and material availability",
    ),
    "capacity_status": (
        "Work Center Utilization",
        "work center utilization and scheduling",
    ),
    "delay_analysis": ("Delay Causes & Trends", "delay causes and trend analysis"),
    "feasibility_check": ("MO Feasibility Scoring", "MO feasibility scoring"),
    "resolution_help": (
        "Resolution Strategies",
        "resolution strategies and scenario comparison",
    ),
    "general": ("General Manufacturing", "general manufacturing information"),
}

_INTENT_DATA_FETCHERS = {
    "demand_query": _fetch_demand_data,
    "material_status": _fetch_material_status,
    "capacity_status": _fetch_capacity_data,
    "delay_analysis": _fetch_delay_analysis,
    "feasibility_check": _fetch_feasibility_data,
    "resolution_help": _fetch_resolution_help,
}


async def route_query(query: str, tenant_id: str) -> dict:
    intent = await _classify_intent(query)
    _topic, hint = _INTENT_HANDLERS.get(
        intent, ("General Manufacturing", "general manufacturing information")
    )

    fetcher = _INTENT_DATA_FETCHERS.get(intent)
    structured_data = await fetcher(query) if fetcher else {}
    system_context = str(structured_data) if isinstance(structured_data, dict) else structured_data

    system_msg = (
        f"You are a manufacturing copilot assistant for tenant {tenant_id}. "
        f"The user's intent is '{intent}' — {hint}. "
        "Be concise and data-driven. "
        f"Here is the current system context you should use to answer: {system_context}\n"
        "If the data is insufficient, explain what specific information the user should provide."
    )

    response = await query_llm(query, system_prompt=system_msg)

    return {
        "intent": intent,
        "response": response,
        "structured_data": structured_data if isinstance(structured_data, dict) else {},
        "sources": [f"nlp-svc:{intent}", f"system-context:{intent}"],
    }
