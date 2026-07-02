"""HTTP request audit middleware — logs mutating API calls to cdm_audit_log + Kafka."""

from __future__ import annotations

import logging
import uuid
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from ipe_shared.audit.service import log_audit_event
from ipe_shared.config import settings

logger = logging.getLogger("ipe.audit")

_AUDIT_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})
_SKIP_PATHS = (
    "/api/v1/health",
    "/metrics",
    "/docs",
    "/openapi.json",
    "/api/v1/auth/login",
    "/api/v1/auth/refresh",
    "/api/v1/auth/info",
)


def _should_audit(request: Request) -> bool:
    if request.method not in _AUDIT_METHODS:
        return False
    path = request.url.path
    return not any(path.startswith(p) for p in _SKIP_PATHS)


def _actor_from_request(request: Request) -> tuple[str, str]:
    auth = request.headers.get("authorization", "")
    tenant = request.headers.get("x-tenant-id", "unknown")
    if auth.startswith("Bearer "):
        return "user", auth[7:20] + "..."
    return "anonymous", "anonymous"


class AuditRequestMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if not settings.AUDIT_REQUEST_MIDDLEWARE or not _should_audit(request):
            return await call_next(request)

        response = await call_next(request)
        tenant_id = request.headers.get("x-tenant-id") or getattr(
            request.state, "tenant_id", "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"
        )
        actor_type, actor_id = _actor_from_request(request)
        entity_id = str(uuid.uuid4())

        try:
            await log_audit_event(
                tenant_id=tenant_id,
                actor_type=actor_type,
                actor_id=actor_id,
                action=f"HTTP_{request.method}",
                entity_type="api_request",
                entity_id=entity_id,
                after_state={
                    "path": request.url.path,
                    "method": request.method,
                    "status": response.status_code,
                    "correlation_id": getattr(request.state, "correlation_id", None),
                },
                rationale=f"{request.method} {request.url.path}",
            )
        except Exception as exc:
            logger.warning("Audit middleware write failed: %s", exc)

        return response
