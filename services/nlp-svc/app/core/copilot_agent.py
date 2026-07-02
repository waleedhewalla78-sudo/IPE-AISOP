"""Planner Copilot Agent: orchestrates LLM tool calls and manages conversation."""

import json
from collections.abc import AsyncGenerator

from app.core.copilot_tools import TOOL_DEFINITIONS, TOOL_HANDLERS
from app.core.llm_client import get_tool_agent_backend
from app.core.ollama_tool_client import OllamaToolClient, anthropic_tool_defs_to_ollama
from app.core.tool_agent_backend import ToolAgentBackend
from ipe_shared.security.pii import strip_pii_from_prompt

SYSTEM_PROMPT = """You are a production planning AI copilot. You help planners understand schedules,
simulate disruptions, and analyze capacity utilization.

You have access to tools that can query production data and run what-if simulations.
IMPORTANT: You can ONLY read data or trigger isolated scenario simulations.
You CANNOT modify, update, or delete any live production records.

When a user asks about a specific order, use get_order_status to check its status.
When a user asks about machine utilization, use get_resource_utilization.
When a user asks "what if" or wants to simulate a breakdown, use simulate_disruption.

Always explain your findings clearly and suggest actionable next steps when appropriate.
Be concise but thorough.
"""

_NOT_CONFIGURED_MSG = (
    "LLM service not configured. Set IPE_OLLAMA_ENDPOINT_URL (recommended) or IPE_ANTHROPIC_API_KEY."
)


async def _run_anthropic_tool_loop(
    backend: ToolAgentBackend,
    clean_query: str,
    tenant_id: str,
    max_iterations: int,
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
                system=SYSTEM_PROMPT,
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

                tool_results = []
                for tool_use in tool_uses:
                    tool_name = tool_use.name
                    tool_input = tool_use.input
                    yield {"type": "tool_call", "tool": tool_name, "input": tool_input}

                    handler = TOOL_HANDLERS.get(tool_name)
                    if handler:
                        result = await handler(tenant_id=tenant_id, **tool_input)
                    else:
                        result = {"error": f"Unknown tool: {tool_name}"}

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
                system_prompt=SYSTEM_PROMPT,
                max_tokens=max_tokens,
            )

            if turn.stop_reason == "end_turn":
                yield {"type": "response", "content": turn.text or "No response generated."}
                return

            if turn.stop_reason == "tool_use" and turn.tool_calls:
                OllamaToolClient.append_assistant_message(messages, turn.raw_message)

                tool_results_payload: list[dict] = []
                for tc in turn.tool_calls:
                    yield {"type": "tool_call", "tool": tc.name, "input": tc.arguments}

                    handler = TOOL_HANDLERS.get(tc.name)
                    if handler:
                        result = await handler(tenant_id=tenant_id, **tc.arguments)
                    else:
                        result = {"error": f"Unknown tool: {tc.name}"}

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


async def run_agent_with_tools(
    query: str,
    tenant_id: str,
    max_iterations: int = 5,
) -> AsyncGenerator[dict, None]:
    """Run the LLM agent with tool calling in a loop."""
    backend = get_tool_agent_backend()
    if backend is None:
        yield {"type": "response", "content": _NOT_CONFIGURED_MSG}
        return

    clean_query, redacted = strip_pii_from_prompt(query)
    if redacted:
        import logging

        logging.getLogger(__name__).info("PII stripped from copilot query: types=%s", redacted)

    if backend.provider == "ollama":
        async for event in _run_ollama_tool_loop(backend, clean_query, tenant_id, max_iterations):
            yield event
    else:
        async for event in _run_anthropic_tool_loop(backend, clean_query, tenant_id, max_iterations):
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
