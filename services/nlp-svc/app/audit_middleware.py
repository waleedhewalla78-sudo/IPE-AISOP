"""Best-effort Copilot audit writer (append-only). Failure never blocks the user response."""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import re
import time
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

_MO_RE = re.compile(r"\bMO[-_][A-Z0-9-]+\b", re.I)
_WC_RE = re.compile(r"\bWC[-_][A-Z0-9-]+\b", re.I)


def parse_sources(text_value: str) -> list[dict[str, str]]:
    sources: list[dict[str, str]] = []
    for m in _MO_RE.findall(text_value or ""):
        sources.append({"entity_type": "manufacturing_order", "entity_id": m})
    for m in _WC_RE.findall(text_value or ""):
        sources.append({"entity_type": "work_center", "entity_id": m})
    return sources


def integrity_hash(
    query_id: str,
    query_text: str,
    response_text: str,
    created_at_epoch: int,
    tenant_id: str,
    secret: str | None = None,
) -> str:
    key = (secret or os.environ.get("COPILOT_AUDIT_HMAC_SECRET") or "ipe-lab-audit-hmac").encode()
    msg = f"{query_id}|{query_text}|{response_text}|{created_at_epoch}|{tenant_id}".encode()
    return hmac.new(key, msg, hashlib.sha256).hexdigest()


def verify_integrity(row: dict[str, Any], secret: str | None = None) -> bool:
    expected = integrity_hash(
        str(row["query_id"]),
        str(row.get("query_text") or ""),
        str(row.get("response_text") or ""),
        int(row["created_at_epoch"]),
        str(row["tenant_id"]),
        secret,
    )
    return hmac.compare_digest(expected, str(row.get("integrity_hash") or ""))


async def write_copilot_audit(
    session: AsyncSession,
    *,
    tenant_id: str,
    query_text: str,
    response_text: str,
    query_mode: str = "ask",
    user_id: str | None = None,
    session_id: str | None = None,
    query_context: dict[str, Any] | None = None,
    llm_provider: str | None = None,
    llm_model: str | None = None,
    llm_latency_ms: int | None = None,
    sources: list[dict[str, str]] | None = None,
) -> UUID | None:
    query_id = uuid4()
    epoch = int(time.time())
    src = sources if sources is not None else parse_sources(query_text + " " + (response_text or ""))
    digest = integrity_hash(str(query_id), query_text, response_text or "", epoch, tenant_id)
    try:
        await session.execute(text("SELECT set_config('app.current_tenant_id', :tid, false)"), {"tid": tenant_id})
        await session.execute(
            text(
                """
                INSERT INTO cdm_copilot_audit (
                  tenant_id, user_id, session_id, query_id, query_text, query_mode,
                  query_context, response_text, response_sources, llm_provider, llm_model,
                  llm_latency_ms, integrity_hash, created_at_epoch
                ) VALUES (
                  CAST(:tid AS uuid), :uid, CAST(:sid AS uuid), CAST(:qid AS uuid), :qtext, :mode,
                  CAST(:ctx AS jsonb), :rtext, CAST(:src AS jsonb), :prov, :model,
                  :lat, :ihash, :epoch
                )
                """
            ),
            {
                "tid": tenant_id,
                "uid": user_id,
                "sid": session_id,
                "qid": str(query_id),
                "qtext": query_text,
                "mode": query_mode,
                "ctx": json.dumps(query_context or {}),
                "rtext": response_text,
                "src": json.dumps(src),
                "prov": llm_provider,
                "model": llm_model,
                "lat": llm_latency_ms,
                "ihash": digest,
                "epoch": epoch,
            },
        )
        await session.commit()
        return query_id
    except Exception:
        logger.exception("copilot audit write failed; returning response anyway")
        try:
            await session.rollback()
        except Exception:
            pass
        return None
