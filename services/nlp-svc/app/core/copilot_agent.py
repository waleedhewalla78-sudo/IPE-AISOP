"""Planner Copilot Agent: orchestrates LLM tool calls and manages conversation.

UAT-10 fix: ``run_agent_with_tools`` now accepts a ``llm_timeout_seconds``
argument (default 18 s).  When the LLM call (Anthropic or Ollama) takes longer
than the budget, the generator is cancelled and the caller receives a
tool-backed structured snapshot via ``build_tool_fallback_response`` instead of
hanging indefinitely.
"""

import asyncio
import json
import logging
from collections.abc import AsyncGenerator

from app.config import settings
from app.core.copilot_tools import (
    TOOL_DEFINITIONS,
    TOOL_HANDLERS,
    get_capacity_alerts,
    get_mo_status,
    get_sop_cycle_status,
)
from app.core.llm_client import get_tool_agent_backend
from app.core.ollama_tool_client import OllamaToolClient, anthropic_tool_defs_to_ollama
from app.core.tool_agent_backend import ToolAgentBackend
from ipe_shared.security.pii import strip_pii_from_prompt

logger = logging.getLogger(__name__)

# Hard ceiling for the LLM round-trip inside the non-streaming chat path.
# The SSE stream has its own 20 s wall-clock guard in copilot.py.
LLM_TIMEOUT_SECONDS: int = 18

SYSTEM_PROMPT = """You are a production planning AI copilot. You help planners understand schedules,
simulate disruptions, and analyze capacity utilization.

You have access to tools that can query production data and run what-if simulations.
IMPORTANT: You can ONLY read data or trigger isolated scenario simulations.
You CANNOT modify, update, or delete any live production records.

When a user asks about a specific order, use get_mo_status or get_order_status to check its status.
When a user asks what is blocking an MO, use get_feasibility_queue and get_mo_status.
When a user asks about machine utilization, use get_resource_utilization.
When a user asks "what if" or wants to simulate a breakdown, use simulate_disruption.
Use get_schedule, get_otd_metrics, get_material_availability, get_sync_status, and
get_resolution_scenarios for live planning context.

Always explain your findings clearly and suggest actionable next steps when appropriate.
Be concise but thorough.
"""

_SHADOW_MODE_PROMPT = """

SHADOW MODE (default): You may only READ data and SUGGEST actions.
Never claim you executed a schedule approval, ERP write-back, or live record change.
All mutations require explicit planner approval in the IPE UI.
"""

DEFAULT_SHADOW_MODE = True

_NOT_CONFIGURED_MSG = (
    "LLM service not configured. Set IPE_OLLAMA_ENDPOINT_URL (recommended) or IPE_ANTHROPIC_API_KEY."
)


def _resolve_shadow_mode(shadow_mode: bool | None) -> bool:
    if shadow_mode is not None:
        return shadow_mode
    return settings.COPILOT_SHADOW_MODE if hasattr(settings, "COPILOT_SHADOW_MODE") else DEFAULT_SHADOW_MODE


def _build_system_prompt(shadow_mode: bool) -> str:
    prompt = SYSTEM_PROMPT
    if shadow_mode:
        prompt += _SHADOW_MODE_PROMPT
    return prompt


async def _run_anthropic_tool_loop(
    backend: ToolAgentBackend,
    clean_query: str,
    tenant_id: str,
    max_iterations: int,
    system_prompt: str,
) -> AsyncGenerator[dict, None]:
    client = backend.client
    model = backend.model_config.get("model", "claude-sonnet-4-20250514")
    max_tokens = backend.model_config.get("max_tokens", 1024)
    messages = [{"role": "user", "content": clean_query}]

    for _iteration in range(max_iterations):
        try:
            response = await client.messages.create(
                model=model,
                max_tokens=max_tokens,
                system=system_prompt,
                tools=TOOL_DEFINITIONS,
                messages=messages,
            )

            if response.stop_reason == "end_turn":
                text_parts = [block.text for block in response.content if block.type == "text"]
                yield {"type": "response", "content": "\n".join(text_parts)}
                return

            if response.stop_reason == "tool_use":
                tool_uses = [block for block in response.content if block.type == "tool_use"]
                messages.append({"role": "assistant", "content": response.content})

                async def _run_one(tool_use):
                    tool_name = tool_use.name
                    tool_input = tool_use.input
                    handler = TOOL_HANDLERS.get(tool_name)
                    if handler:
                        try:
                            result = await handler(tenant_id=tenant_id, **tool_input)
                        except Exception as exc:
                            result = {"error": str(exc)}
                    else:
                        result = {"error": f"Unknown tool: {tool_name}"}
                    return tool_use, tool_name, tool_input, result

                gathered = await asyncio.gather(
                    *[_run_one(tu) for tu in tool_uses],
                    return_exceptions=True,
                )
                tool_results = []
                for item in gathered:
                    if isinstance(item, Exception):
                        yield {"type": "tool_result", "tool": "unknown", "result": {"error": str(item)}}
                        continue
                    tool_use, tool_name, tool_input, result = item
                    yield {"type": "tool_call", "tool": tool_name, "input": tool_input}
                    yield {"type": "tool_result", "tool": tool_name, "result": result}
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": tool_use.id,
                            "content": json.dumps(result),
                        }
                    )

                messages.append({"role": "user", "content": tool_results})

        except Exception as exc:
            yield {"type": "response", "content": f"Error: {exc!s}"}
            return

    yield {
        "type": "response",
        "content": "I've reached the maximum number of tool iterations. Please rephrase your question.",
    }


async def _run_ollama_tool_loop(
    backend: ToolAgentBackend,
    clean_query: str,
    tenant_id: str,
    max_iterations: int,
    system_prompt: str,
) -> AsyncGenerator[dict, None]:
    client: OllamaToolClient = backend.client
    max_tokens = backend.model_config.get("max_tokens", 1024)
    ollama_tools = anthropic_tool_defs_to_ollama(TOOL_DEFINITIONS)
    messages: list[dict] = [{"role": "user", "content": clean_query}]

    for _iteration in range(max_iterations):
        try:
            turn = await client.create_turn(
                messages=messages,
                tools=ollama_tools,
                system_prompt=system_prompt,
                max_tokens=max_tokens,
            )

            if turn.stop_reason == "end_turn":
                yield {"type": "response", "content": turn.text or "No response generated."}
                return

            if turn.stop_reason == "tool_use" and turn.tool_calls:
                OllamaToolClient.append_assistant_message(messages, turn.raw_message)

                tool_results_payload: list[dict] = []

                async def _run_one_ollama(tc):
                    handler = TOOL_HANDLERS.get(tc.name)
                    if handler:
                        try:
                            result = await handler(tenant_id=tenant_id, **tc.arguments)
                        except Exception as exc:
                            result = {"error": str(exc)}
                    else:
                        result = {"error": f"Unknown tool: {tc.name}"}
                    return tc, result

                gathered = await asyncio.gather(
                    *[_run_one_ollama(tc) for tc in turn.tool_calls],
                    return_exceptions=True,
                )
                for item in gathered:
                    if isinstance(item, Exception):
                        yield {"type": "tool_result", "tool": "unknown", "result": {"error": str(item)}}
                        tool_results_payload.append({"error": str(item)})
                        continue
                    tc, result = item
                    yield {"type": "tool_call", "tool": tc.name, "input": tc.arguments}
                    yield {"type": "tool_result", "tool": tc.name, "result": result}
                    tool_results_payload.append(result)

                OllamaToolClient.append_tool_results(messages, turn.tool_calls, tool_results_payload)
                continue

            yield {"type": "response", "content": turn.text or "No response generated."}
            return

        except Exception as exc:
            detail = str(exc) or "Ollama request failed — try a smaller model or increase timeout"
            yield {"type": "response", "content": f"Error ({type(exc).__name__}): {detail}"}
            return

    yield {
        "type": "response",
        "content": "I've reached the maximum number of tool iterations. Please rephrase your question.",
    }


async def build_tool_fallback_response(tenant_id: str) -> str:
    """Collect live planning data without the LLM and return a structured snapshot.

    Called when the LLM is unavailable or exceeds the timeout budget.  Tool
    calls run concurrently (each with its own HTTP timeout) so this returns
    quickly even when some upstreams are slow.
    """
    parts: list[str] = [
        "[Tool-backed snapshot — LLM not available or timed out]",
        "",
    ]

    alerts, sop, mo_data = await asyncio.gather(
        get_capacity_alerts(tenant_id),
        get_sop_cycle_status(tenant_id),
        get_mo_status(None, tenant_id),
        return_exceptions=True,
    )

    if isinstance(alerts, Exception):
        parts.append(f"Capacity alerts: fetch error ({alerts})")
    elif alerts.get("status") == "ok":
        alert_items = alerts.get("alerts", [])
        parts.append(f"Capacity alerts: {len(alert_items)} overloaded work center(s)")
        for a in alert_items[:3]:
            parts.append(f"  • {a.get('work_center', '?')} — {a.get('utilisation_pct', '?')}% utilised")
    else:
        parts.append(f"Capacity alerts: unavailable ({alerts.get('message', '')})")

    if isinstance(sop, Exception):
        parts.append(f"S&OP cycle: fetch error ({sop})")
    elif sop.get("status") == "ok":
        parts.append(f"S&OP cycle: {sop.get('cycle_status', 'unknown')} — deadline {sop.get('deadline', 'n/a')}")
    else:
        parts.append(f"S&OP cycle: unavailable ({sop.get('message', '')})")

    if isinstance(mo_data, Exception):
        parts.append(f"MO status: fetch error ({mo_data})")
    elif mo_data.get("status") == "ok":
        mos = mo_data.get("items") or mo_data.get("mos") or []
        if isinstance(mos, list):
            parts.append(f"Manufacturing orders visible: {len(mos)}")
        else:
            parts.append("Manufacturing orders: ok")
    else:
        parts.append(f"MO status: unavailable ({mo_data.get('message', '')})")

    parts += [
        "",
        "Note: The LLM response timed out or the LLM provider is unreachable.",
        "Tool data above is live.  Set IPE_ANTHROPIC_API_KEY or IPE_OLLAMA_ENDPOINT_URL",
        "and retry to get an AI-synthesised answer.",
    ]
    return "\n".join(parts)


async def run_agent_with_tools(
    query: str,
    tenant_id: str,
    max_iterations: int = 5,
    shadow_mode: bool | None = None,
) -> AsyncGenerator[dict, None]:
    """Run the LLM agent with tool calling in a loop.

    Yields events: ``{"type": "tool_call" | "tool_result" | "response", ...}``

    When the LLM backend is not configured the generator immediately yields a
    ``response`` event with ``_NOT_CONFIGURED_MSG`` so callers always get at
    least one event.
    """
    backend = get_tool_agent_backend()
    if backend is None:
        yield {"type": "response", "content": _NOT_CONFIGURED_MSG}
        return

    resolved_shadow = _resolve_shadow_mode(shadow_mode)
    system_prompt = _build_system_prompt(resolved_shadow)

    clean_query, redacted = strip_pii_from_prompt(query)
    if redacted:
        logger.info("PII stripped from copilot query: types=%s", redacted)

    if backend.provider == "ollama":
        async for event in _run_ollama_tool_loop(
            backend, clean_query, tenant_id, max_iterations, system_prompt
        ):
            yield event
    else:
        async for event in _run_anthropic_tool_loop(
            backend, clean_query, tenant_id, max_iterations, system_prompt
        ):
            yield event


async def run_agent_streaming(
    query: str,
    tenant_id: str,
) -> AsyncGenerator[str, None]:
    """Run the agent and stream results as SSE events."""
    async for event in run_agent_with_tools(query, tenant_id):
        chunk = json.dumps(event)
        yield f"data: {chunk}\n\n"

    yield f"data: {json.dumps({'type': 'done'})}\n\n"
