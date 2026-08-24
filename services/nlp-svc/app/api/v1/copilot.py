"""Enhanced Copilot endpoint with tool calling and scenario simulation.

UAT-10 fix: both the streaming (SSE) and non-streaming /chat paths now enforce
a hard 20-second wall-clock budget.  When the LLM is unavailable or slow the
non-streaming path returns a tool-backed structured snapshot via
``build_tool_fallback_response`` within that window.
"""

import asyncio
import json
import logging
import time
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.copilot_agent import build_tool_fallback_response, run_agent_streaming, run_agent_with_tools
from ipe_shared.audit.service import log_audit_event
from ipe_shared.auth.jwt import TokenPayload
from ipe_shared.auth.rbac import require_roles
from ipe_shared.database.session import get_session
from ipe_shared.events.producer import kafka_producer
from ipe_shared.events.schemas import EventEnvelope
from ipe_shared.middleware.tenant_context import tenant_ctx
from ipe_shared.schemas.common import APIResponse

logger = logging.getLogger(__name__)

_TIMEOUT_SECONDS = 20          # wall-clock budget for both SSE and non-streaming paths
_HEARTBEAT_INTERVAL = 15
_MAX_BUFFER_SIZE = 100

router = APIRouter(prefix="/copilot", tags=["copilot"])


class ChatRequest(BaseModel):
    message: str
    stream: bool = False
    session_id: str | None = None
    role: str | None = None


class QueryRequest(BaseModel):
    query: str
    stream: bool = False
    session_id: str | None = None
    role: str | None = None


class SessionCreateRequest(BaseModel):
    role: str | None = None


async def _sse_stream(message: str, tenant_id: str) -> AsyncGenerator[str, None]:
    """Stream agent responses as SSE events with edge case handling.

    Handles:
    - Client disconnect via CancelledError cleanup
    - 30-second timeout with partial response and status: "timeout"
    - Error recovery mid-stream via event: error
    - Backpressure with 100-event buffer and event: dropped
    - Heartbeat ping every 15 seconds (event: ping)
    """
    queue: asyncio.Queue[str | object] = asyncio.Queue(maxsize=_MAX_BUFFER_SIZE)
    _done_sentinel = object()
    dropped_count = 0
    start_time = time.monotonic()

    async def _producer() -> None:
        nonlocal dropped_count
        try:
            async for sse_event in run_agent_streaming(message, tenant_id):
                try:
                    queue.put_nowait(sse_event)
                except asyncio.QueueFull:
                    dropped_count += 1
                    try:
                        queue.get_nowait()
                    except asyncio.QueueEmpty:
                        logger.debug("SSE backpressure: queue already empty when trying to drop oldest event")
                    dropped_event = (
                        f"event: dropped\ndata: "
                        f"{json.dumps({'dropped_count': dropped_count})}\n\n"
                    )
                    try:
                        queue.put_nowait(dropped_event)
                    except asyncio.QueueFull:
                        logger.warning("SSE backpressure: could not enqueue dropped-event marker")
        except asyncio.CancelledError:
            logger.info("SSE producer cancelled (client disconnect)")
        except Exception as exc:
            logger.exception("SSE stream error: %s", exc)
            error_event = (
                f"event: error\ndata: "
                f"{json.dumps({'error': str(exc)})}\n\n"
            )
            try:
                queue.put_nowait(error_event)
            except asyncio.QueueFull:
                logger.warning("SSE backpressure: could not enqueue error event for %s", exc)
        finally:
            try:
                queue.put_nowait(_done_sentinel)
            except asyncio.QueueFull:
                try:
                    queue.get_nowait()
                except asyncio.QueueEmpty:
                    logger.debug("SSE done-sentinel fallback: queue already empty")
                try:
                    queue.put_nowait(_done_sentinel)
                except asyncio.QueueFull:
                    logger.warning("SSE backpressure: could not enqueue done sentinel")

    async def _heartbeat() -> None:
        while True:
            await asyncio.sleep(_HEARTBEAT_INTERVAL)
            try:
                queue.put_nowait("event: ping\ndata: {}\n\n")
            except asyncio.QueueFull:
                logger.debug("SSE heartbeat: queue full, skipping ping")

    producer_task = asyncio.create_task(_producer())
    heartbeat_task = asyncio.create_task(_heartbeat())

    try:
        while True:
            elapsed = time.monotonic() - start_time
            if elapsed >= _TIMEOUT_SECONDS:
                yield f"data: {json.dumps({'type': 'partial', 'status': 'timeout'})}\n\n"
                break

            remaining = _TIMEOUT_SECONDS - elapsed
            try:
                event = await asyncio.wait_for(
                    queue.get(), timeout=min(remaining, 1.0),
                )
            except asyncio.TimeoutError:
                continue

            if event is _done_sentinel:
                break

            yield event
    except asyncio.CancelledError:
        logger.info("SSE stream cancelled (client disconnect), cleaning up")
    finally:
        producer_task.cancel()
        heartbeat_task.cancel()
        for _t in (producer_task, heartbeat_task):
            try:
                await _t
            except (asyncio.CancelledError, Exception):
                logger.debug("SSE cleanup: task %s finished with exception", _t.get_name())


@router.post("/chat")
async def copilot_chat(
    req: ChatRequest,
    current_user: TokenPayload = Depends(require_roles(["planner", "admin", "manager", "supervisor"])),
):
    """Chat endpoint with LLM tool calling for scenario simulation.

    Supports both streaming (SSE) and non-streaming responses.
    The LLM can call tools to query orders, check utilization, and simulate disruptions.
    """
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(
            success=False, data=None,
            error={"code": "NO_TENANT", "message": "No tenant context"},
        )

    if req.stream:
        return StreamingResponse(
            _sse_stream(req.message, tenant_id),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
                "Connection": "keep-alive",
            },
        )

    # Non-streaming path: enforce a hard 20 s timeout so the endpoint never
    # hangs when the LLM is slow or unreachable.
    timed_out = False
    try:
        async with asyncio.timeout(_TIMEOUT_SECONDS):
            events = []
            async for event in run_agent_with_tools(req.message, tenant_id):
                events.append(event)
    except asyncio.TimeoutError:
        timed_out = True
        logger.warning(
            "copilot /chat LLM timeout after %ds; returning tool fallback for tenant %s",
            _TIMEOUT_SECONDS,
            tenant_id,
        )
        fallback_text = await build_tool_fallback_response(tenant_id)
        events = [{"type": "response", "content": fallback_text}]

    final_response = next(
        (e["content"] for e in reversed(events) if e["type"] == "response"),
        "No response generated.",
    )
    tool_calls = [e for e in events if e["type"] == "tool_call"]

    await kafka_producer.send_event(
        "copilot", "chat",
        key=tenant_id,
        value=EventEnvelope(
            event_id=str(uuid4()),
            event_type="ipe.copilot.chat",
            source="nlp-svc",
            tenant_id=tenant_id,
            timestamp=datetime.now(UTC),
            data={
                "message_length": len(req.message),
                "response_length": len(final_response),
                "tools_used": [tc["tool"] for tc in tool_calls],
            },
        ).model_dump(mode="json"),
    )

    await log_audit_event(
        tenant_id=tenant_id,
        actor_type="user",
        actor_id=str(current_user.sub),
        action="COPILOT_CHAT",
        entity_type="copilot_query",
        entity_id=uuid4(),
        before_state={"message": req.message[:500]},
        after_state={
            "response_length": len(final_response),
            "tools_used": [tc["tool"] for tc in tool_calls],
        },
        rationale=f"User copilot chat, {len(tool_calls)} tool calls",
    )

    return APIResponse(
        success=True,
        data={
            "response": final_response,
            "tool_calls": tool_calls,
            **({"timeout": True} if timed_out else {}),
        },
        error=None,
    )


@router.post("/query")
async def copilot_query(
    req: QueryRequest,
    request: Request,
    db: AsyncSession = Depends(get_session),
    current_user: TokenPayload = Depends(require_roles(["planner", "admin", "manager", "supervisor", "auditor"])),
):
    """Legacy query endpoint (backward compatible with Sprint 4 copilot)."""
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(
            success=False, data=None,
            error={"code": "NO_TENANT", "message": "No tenant context"},
        )

    from app.core.orchestrator import route_query
    from app.core.llm_errors import LLMUnavailableError
    from app.core.role_agents import resolve_agent
    from app.core.copilot_session import append_turn
    from uuid import UUID as PyUUID

    auth_header = request.headers.get("Authorization")
    agent = resolve_agent(req.role or getattr(current_user, "role", None))
    try:
        result = await route_query(req.query, tenant_id, auth_header=auth_header)
    except LLMUnavailableError as exc:
        return JSONResponse(
            status_code=503,
            content=APIResponse(
                success=False,
                data=None,
                error={"code": "LLM_UNAVAILABLE", "message": str(exc)},
            ).model_dump(mode="json"),
        )

    await kafka_producer.send_event(
        "copilot", "queried",
        key=tenant_id,
        value=EventEnvelope(
            event_id=str(uuid4()),
            event_type="ipe.copilot.queried",
            source="nlp-svc",
            tenant_id=tenant_id,
            timestamp=datetime.now(UTC),
            data={
                "intent": result["intent"],
                "response_length": len(result["response"]),
            },
        ).model_dump(mode="json"),
    )

    if req.session_id:
        await append_turn(
            db,
            tenant_id=tenant_id,
            session_id=PyUUID(req.session_id),
            user_message=req.query,
            assistant_message=result.get("response", ""),
            intent=result.get("intent"),
        )
        await db.commit()

    result["agent_role"] = agent.role
    result["follow_up_suggestions"] = list(agent.follow_up_suggestions)

    try:
        from app.audit_middleware import write_copilot_audit

        await write_copilot_audit(
            db,
            tenant_id=tenant_id,
            query_text=req.query,
            response_text=str(result.get("response") or ""),
            query_mode="ask",
            user_id=getattr(current_user, "sub", None) or getattr(current_user, "user_id", None),
            session_id=req.session_id,
            query_context={"intent": result.get("intent"), "role": req.role},
            llm_provider=str(result.get("provider") or result.get("llm_provider") or ""),
        )
    except Exception:
        logger.exception("copilot audit skipped")

    return APIResponse(success=True, data=result, error=None)


@router.get("/llm-status")
async def copilot_llm_status(
    current_user: TokenPayload = Depends(require_roles(["admin", "manager"])),
):
    """Return active LLM tier and provider health for admin console."""
    tenant_id = tenant_ctx.get() or ""
    from app.core.llm_client import get_llm_status

    status = await get_llm_status(tenant_id)
    return APIResponse(success=True, data=status, error=None)


@router.get("/agents")
async def copilot_agents(
    current_user: TokenPayload = Depends(require_roles(["planner", "admin", "manager", "supervisor", "executive", "auditor"])),
):
    from app.core.role_agents import list_agents_for_role

    user_role = getattr(current_user, "role", None) or "planner"
    return APIResponse(success=True, data={"agents": list_agents_for_role(str(user_role))}, error=None)


@router.post("/session")
async def copilot_create_session(
    req: SessionCreateRequest,
    db: AsyncSession = Depends(get_session),
    current_user: TokenPayload = Depends(require_roles(["planner", "admin", "manager", "supervisor", "executive"])),
):
    from uuid import UUID as PyUUID

    from app.core.copilot_session import create_session
    from app.core.role_agents import resolve_agent
    from sqlalchemy.ext.asyncio import AsyncSession

    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})

    agent = resolve_agent(req.role or getattr(current_user, "role", None))
    row = await create_session(
        db,
        tenant_id=tenant_id,
        user_id=PyUUID(str(current_user.sub)),
        role=agent.role,
        context={"follow_up_suggestions": list(agent.follow_up_suggestions)},
    )
    await db.commit()
    return APIResponse(
        success=True,
        data={
            "session_id": str(row.id),
            "role": row.role,
            "agent": agent.label,
            "follow_up_suggestions": list(agent.follow_up_suggestions),
        },
        error=None,
    )

