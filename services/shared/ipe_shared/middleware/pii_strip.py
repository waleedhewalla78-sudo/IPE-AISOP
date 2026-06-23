"""FastAPI middleware that strips PII from LLM prompt request bodies."""
from __future__ import annotations

import json
import logging

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from ipe_shared.security.pii import PIIStripper

logger = logging.getLogger("ipe.pii_strip")

_STRIPPABLE_PATHS = ("copilot", "classify", "query")

_stripper = PIIStripper()


class PIIStripMiddleware(BaseHTTPMiddleware):
    """Intercepts request bodies on LLM prompt endpoints and strips PII
    before the request reaches the handler."""

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if not any(segment in path for segment in _STRIPPABLE_PATHS):
            return await call_next(request)

        if request.method.upper() != "POST":
            return await call_next(request)

        body = await request.body()
        if not body:
            return await call_next(request)

        try:
            data = json.loads(body)
        except (json.JSONDecodeError, UnicodeDecodeError):
            return await call_next(request)

        stripped_data, redacted_types = _stripper.strip_with_report(
            json.dumps(data)
        )
        if not redacted_types:
            return await call_next(request)

        logger.info(
            "pii_stripped path=%s types=%s", path, ",".join(redacted_types)
        )

        try:
            stripped_data_obj = json.loads(stripped_data)
        except json.JSONDecodeError:
            stripped_data_obj = data

        if isinstance(stripped_data_obj, dict):
            stripped_data_obj = _stripper.strip_dict(stripped_data_obj)

        new_body = json.dumps(stripped_data_obj).encode("utf-8")

        async def receive():
            return {"type": "http.request", "body": new_body}

        request._receive = receive
        return await call_next(request)