"""Query routing orchestrator with intent classification and service aggregation."""

import json

import httpx

from app.config import settings
from app.core.llm_client import query_llm
from app.core.llm_errors import LLMUnavailableError
from app.core.response_formatter import format_structured_response, is_llm_error

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

_KEYWORD_INTENTS: dict[str, tuple[str, ...]] = {
    "material_status": (
        "stock", "inventory", "fg", "finished good", "finished goods", "on hand",
        "on-hand", "material", "qty", "quantity", "warehouse", "raw material",
    ),
    "demand_query": ("demand", "customer order", "sales order", "due date", "priority"),
    "capacity_status": ("capacity", "utilization", "bottleneck", "work center", "overload"),
    "delay_analysis": ("delay", "late", "disruption", "behind schedule", "cause"),
    "feasibility_check": ("feasibility", "at risk", "risk score", "feasible", "constraint"),
    "resolution_help": ("resolution", "scenario", "mitigation", "expedite", "overtime", "substitute"),
}

_SERVICE_URLS: dict[str, str] = {
    "dpe": settings.DPE_SVC_URL,
    "mat": settings.MAT_SVC_URL,
    "cap": settings.CAP_SVC_URL,
    "fea": settings.FEA_SVC_URL,
    "res": settings.RES_SVC_URL,
}


def _auth_headers(tenant_id: str, auth_header: str | None) -> dict[str, str]:
    headers = {"X-Tenant-ID": tenant_id}
    if auth_header:
        headers["Authorization"] = auth_header
    return headers


def _classify_intent_keywords(query: str) -> str | None:
    lowered = query.lower()
    for intent, keywords in _KEYWORD_INTENTS.items():
        if any(keyword in lowered for keyword in keywords):
            return intent
    return None


async def _classify_intent(query: str) -> str:
    keyword_intent = _classify_intent_keywords(query)
    if keyword_intent:
        return keyword_intent

    llm_response = await query_llm(_INTENT_PROMPT + f"Query: {query}")
    for intent in _INTENTS:
        if intent in llm_response.lower():
            return intent
    return "general"


async def _fetch_demand_data(tenant_id: str, _query: str = "", auth_header: str | None = None) -> dict:
    try:
        async with httpx.AsyncClient(timeout=10) as cli:
            headers = _auth_headers(tenant_id, auth_header)
            resp = await cli.get(f"{_SERVICE_URLS['dpe']}/api/v1/dashboard/demands", headers=headers)
            if resp.is_success:
                data = resp.json().get("data", {})
                demands = data.get("demands", [])
                return {"items": demands, "total": len(demands)}
            return {"error": f"Demand query returned {resp.status_code}"}
    except Exception as exc:
        return {"error": f"Could not fetch demand data: {exc}"}


async def _fetch_material_status(tenant_id: str, query: str, auth_header: str | None = None) -> dict:
    try:
        include_purchased = any(
            term in query.lower() for term in ("raw", "component", "purchased", "all material", "all inventory")
        )
        async with httpx.AsyncClient(timeout=10) as cli:
            headers = _auth_headers(tenant_id, auth_header)
            resp = await cli.get(
                f"{_SERVICE_URLS['mat']}/api/v1/material/inventory-summary",
                headers=headers,
                params={"include_purchased": str(include_purchased).lower()},
            )
            if resp.is_success:
                return resp.json().get("data", {})
            return {"error": f"Inventory query returned {resp.status_code}"}
    except Exception as exc:
        return {"error": f"Could not fetch material data: {exc}"}


async def _fetch_capacity_data(tenant_id: str, _query: str = "", auth_header: str | None = None) -> dict:
    try:
        async with httpx.AsyncClient(timeout=20) as cli:
            headers = _auth_headers(tenant_id, auth_header)
            resp = await cli.post(
                f"{_SERVICE_URLS['cap']}/api/v1/capacity/schedule",
                json={"tenant_id": tenant_id},
                headers=headers,
            )
            if resp.is_success:
                data = resp.json().get("data", resp.json())
                return {
                    "bottlenecks": data.get("bottlenecks", []),
                    "total_operations": data.get("total_operations"),
                    "utilization": data.get("utilization", []),
                }
            return {"error": f"Capacity query returned {resp.status_code}"}
    except Exception as exc:
        return {"error": f"Could not fetch capacity data: {exc}"}


async def _fetch_delay_analysis(tenant_id: str, _query: str = "", auth_header: str | None = None) -> dict:
    try:
        async with httpx.AsyncClient(timeout=10) as cli:
            headers = _auth_headers(tenant_id, auth_header)
            resp = await cli.get(f"{_SERVICE_URLS['dpe']}/api/v1/dashboard/alerts", headers=headers)
            if resp.is_success:
                alerts = resp.json().get("data", {}).get("alerts", [])
                return {"alerts": alerts, "total": len(alerts)}
            return {"error": f"Delay query returned {resp.status_code}"}
    except Exception as exc:
        return {"error": f"Could not fetch delay data: {exc}"}


async def _fetch_feasibility_data(tenant_id: str, _query: str = "", auth_header: str | None = None) -> dict:
    try:
        async with httpx.AsyncClient(timeout=10) as cli:
            headers = _auth_headers(tenant_id, auth_header)
            resp = await cli.get(f"{_SERVICE_URLS['fea']}/api/v1/feasibility/queue", headers=headers)
            if resp.is_success:
                payload = resp.json()
                items = payload.get("data") or payload.get("items") or []
                return {"items": items, "total": len(items)}
            return {"error": f"Feasibility query returned {resp.status_code}"}
    except Exception as exc:
        return {"error": f"Could not fetch feasibility data: {exc}"}


async def _fetch_resolution_help(tenant_id: str, _query: str = "", auth_header: str | None = None) -> dict:
    try:
        async with httpx.AsyncClient(timeout=10) as cli:
            headers = _auth_headers(tenant_id, auth_header)
            resp = await cli.get(f"{_SERVICE_URLS['res']}/api/v1/resolution/scenarios", headers=headers)
            if resp.is_success:
                scenarios = resp.json().get("data", {}).get("scenarios", [])
                return {"scenarios": scenarios[:10], "total": len(scenarios)}
            return {"error": f"Resolution query returned {resp.status_code}"}
    except Exception as exc:
        return {"error": f"Could not fetch resolution data: {exc}"}


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


async def route_query(query: str, tenant_id: str, auth_header: str | None = None) -> dict:
    intent = await _classify_intent(query)
    _topic, hint = _INTENT_HANDLERS.get(
        intent, ("General Manufacturing", "general manufacturing information")
    )

    fetcher = _INTENT_DATA_FETCHERS.get(intent)
    structured_data: dict | str = {}
    if fetcher:
        structured_data = await fetcher(tenant_id, query, auth_header)

    system_context = json.dumps(structured_data) if isinstance(structured_data, dict) else str(structured_data)

    system_msg = (
        f"You are a manufacturing copilot assistant for tenant {tenant_id}. "
        f"The user's intent is '{intent}' — {hint}. "
        "Be concise and data-driven. "
        f"Here is the current system context you should use to answer: {system_context}\n"
        "If the data is insufficient, explain what specific information the user should provide."
    )

    response = await query_llm(query, system_prompt=system_msg)
    if is_llm_error(response):
        if settings.LLM_ROUTING_ENABLED:
            raise LLMUnavailableError(response)
        formatted = format_structured_response(intent, structured_data)
        if formatted:
            response = formatted

    return {
        "intent": intent,
        "response": response,
        "structured_data": structured_data if isinstance(structured_data, (dict, list)) else {"summary": structured_data},
        "sources": [f"nlp-svc:{intent}", f"system-context:{intent}"],
    }
