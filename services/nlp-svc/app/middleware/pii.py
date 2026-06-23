"""PII stripping middleware for nlp-svc.

Intercepts request bodies containing text/JSON, strips PII from query
fields in copilot/chat requests, and logs stripping events via the audit
module.

Tenant tier determines stripping behavior:
  - SAAS:       strip PII before sending to external LLM
  - PRIVATE_VPC: strip PII before sending
  - ON_PREM:    no PII stripping (data stays on-premises)
"""
from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

from starlette.middleware.base import BaseHTTPMiddleware

from app.core.tiered_router import LLMTier, TieredRouter
from ipe_shared.audit.service import log_audit_event
from ipe_shared.security.pii import PIIEntity, PIIStripper

if TYPE_CHECKING:
    from starlette.requests import Request

logger = logging.getLogger(__name__)

_TIERED_ROUTER = TieredRouter()
_STRIPPER = PIIStripper()

_PII_STRIP_TIERS: set[LLMTier] = {LLMTier.SAAS, LLMTier.PRIVATE_VPC}

_TEXT_FIELDS: list[str] = [
    "query",
    "message",
]


class PIIStrippingMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware that strips PII from request bodies.

    Applies only to POST requests with JSON bodies that contain a recognized
    text field (query, message).  Stripping is performed based on the
    tenant's LLM tier — SAAS and PRIVATE_VPC tenants have PII removed,
    ON_PREM tenants skip stripping entirely.
    """

    async def dispatch(self, request: Request, call_next):
        if request.method.upper() != "POST":
            return await call_next(request)

        content_type = request.headers.get("content-type", "")
        if "json" not in content_type and "text" not in content_type:
            return await call_next(request)

        try:
            body = await request.body()
            if not body:
                return await call_next(request)

            parsed = json.loads(body)
            if not isinstance(parsed, dict):
                return await call_next(request)

            tenant_id = request.headers.get("X-Tenant-ID", "")

            tier = _TIERED_ROUTER.get_tier(tenant_id)

            if tier not in _PII_STRIP_TIERS:
                return await call_next(request)

            all_entities: list[PIIEntity] = []
            modified = False

            for field_name in _TEXT_FIELDS:
                if field_name in parsed and isinstance(parsed[field_name], str):
                    stripped_text, entities = _STRIPPER.strip_with_entities(parsed[field_name])
                    if entities:
                        parsed[field_name] = stripped_text
                        all_entities.extend(entities)
                        modified = True

            if "system_prompt" in parsed and isinstance(parsed["system_prompt"], str):
                stripped_text, entities = _STRIPPER.strip_with_entities(parsed["system_prompt"])
                if entities:
                    parsed["system_prompt"] = stripped_text
                    all_entities.extend(entities)
                    modified = True

            if modified:
                new_body = json.dumps(parsed).encode("utf-8")

                try:
                    pii_types = list(
                        {e.entity_type for e in all_entities}
                    )
                    await log_audit_event(
                        tenant_id=tenant_id,
                        actor_type="system",
                        actor_id="pii_middleware",
                        action="PII_STRIPPED",
                        entity_type="request",
                        entity_id="",
                        before_state={
                            "pii_types_detected": pii_types,
                        },
                        after_state={
                            "pii_count": len(all_entities),
                            "fields_stripped": pii_types,
                        },
                        rationale=(
                            f"PII stripped for tenant"
                            f" tier {tier.value}"
                        ),
                    )
                except Exception:
                    logger.debug("Audit logging for PII stripping failed (non-critical)")

                async def receive():
                    return {"type": "http.request", "body": new_body}

                request._receive = receive

            return await call_next(request)

        except (json.JSONDecodeError, UnicodeDecodeError):
            return await call_next(request)
        except Exception:
            logger.exception("Unexpected error in PII stripping middleware")
            return await call_next(request)
