"""Planner Copilot Agent: orchestrates LLM tool calls and manages conversation."""

import json
from collections.abc import AsyncGenerator

from app.core.copilot_tools import TOOL_DEFINITIONS, TOOL_HANDLERS
from app.core.llm_client import _get_client
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


async def run_agent_with_tools(
    query: str,
    tenant_id: str,
    max_iterations: int = 5,
) -> AsyncGenerator[dict, None]:
    """Run the LLM agent with tool calling in a loop.

    The agent can call tools up to max_iterations times before responding.
    Each iteration: LLM either calls a tool or provides a final text response.

    Yields:
        Dicts with type: "thinking", "tool_call", "tool_result", or "response".
    """
    client, model_config = _get_client()
    if client is None:
        yield {
            "type": "response",
            "content": "LLM service not configured. Please set ANTHROPIC_API_KEY.",
        }
        return

    model = model_config.get("model", "claude-sonnet-4-20250514")
    max_tokens = model_config.get("max_tokens", 1024)

    clean_query, redacted = strip_pii_from_prompt(query)
    if redacted:
        import logging

        logging.getLogger(__name__).info("PII stripped from copilot query: types=%s", redacted)

    messages = [{"role": "user", "content": clean_query}]

    for iteration in range(max_iterations):
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

        except Exception as e:
            yield {"type": "response", "content": f"Error: {e!s}"}
            return

    yield {
        "type": "response",
        "content": "I've reached the maximum number of tool iterations. Please rephrase your question.",
    }


async def run_agent_streaming(
    query: str,
    tenant_id: str,
) -> AsyncGenerator[str, None]:
    """Run the agent and stream results as SSE events.

    Yields SSE-formatted strings for frontend consumption.
    """
    async for event in run_agent_with_tools(query, tenant_id):
        chunk = json.dumps(event)
        yield f"data: {chunk}\n\n"

    yield f"data: {json.dumps({'type': 'done'})}\n\n"
