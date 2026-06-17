import json
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from uuid import uuid4

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.core.llm_client import stream_llm
from app.core.orchestrator import (
    _INTENT_DATA_FETCHERS,
    _INTENT_HANDLERS,
    _classify_intent,
    route_query,
)
from ipe_shared.events.producer import kafka_producer
from ipe_shared.events.schemas import EventEnvelope
from ipe_shared.middleware.tenant_context import tenant_ctx
from ipe_shared.schemas.common import APIResponse

router = APIRouter(prefix="/copilot", tags=["copilot"])


class QueryRequest(BaseModel):
    query: str
    stream: bool = False


async def _token_generator(query: str, tenant_id: str) -> AsyncGenerator[str, None]:
    intent = await _classify_intent(query)
    _topic, hint = _INTENT_HANDLERS.get(
        intent, ("General Manufacturing", "general manufacturing information")
    )

    fetcher = _INTENT_DATA_FETCHERS.get(intent)
    system_context = await fetcher(query) if fetcher else ""

    system_msg = (
        f"You are a manufacturing copilot assistant for tenant {tenant_id}. "
        f"The user's intent is '{intent}' — {hint}. "
        "Be concise and data-driven. "
        f"Here is the current system context you should use to answer: {system_context}\n"
        "If the data is insufficient, explain what specific information the user should provide."
    )

    async for token in stream_llm(query, system_prompt=system_msg):
        if token:
            chunk = json.dumps({"token": token})
            yield f"data: {chunk}\n\n"

    final = json.dumps({
        "token": "", "done": True, "intent": intent,
        "sources": [f"nlp-svc:{intent}", f"system-context:{intent}"],
    })
    yield f"data: {final}\n\n"


@router.post("/query")
async def copilot_query(req: QueryRequest):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(
            success=False, data=None,
            error={"code": "NO_TENANT", "message": "No tenant context"},
        )

    if req.stream:
        return StreamingResponse(
            _token_generator(req.query, tenant_id),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    result = await route_query(req.query, tenant_id)

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

    return APIResponse(success=True, data=result, error=None)
