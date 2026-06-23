from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

import httpx

from ipe_shared.config import settings

logger = logging.getLogger(__name__)

SEVERITY_MAP: dict[str, str] = {
    "critical": "error",
    "high": "error",
    "medium": "warning",
    "low": "info",
}


@dataclass
class PagerDutyConfig:
    routing_key: str = ""
    severity_map: dict[str, str] = field(default_factory=lambda: dict(SEVERITY_MAP))
    auto_resolve: bool = True


class PagerDutyClient:
    def __init__(self, config: PagerDutyConfig | None = None):
        self._config = config or PagerDutyConfig()
        self._client: httpx.AsyncClient | None = None

    @property
    def routing_key(self) -> str:
        return self._config.routing_key or settings.PAGERDUTY_ROUTING_KEY

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=10.0)
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    def _map_severity(self, severity: str) -> str:
        return self._config.severity_map.get(severity.lower(), "warning")

    async def send_alert(
        self,
        action: str,
        summary: str,
        severity: str = "medium",
        source: str = "ipe",
        component: str = "",
        group: str = "",
        details: dict[str, Any] | None = None,
        incident_key: str | None = None,
    ) -> dict[str, Any] | None:
        if not self.routing_key:
            logger.warning("PagerDuty routing key not configured; skipping alert")
            return None

        if action not in ("trigger", "acknowledge", "resolve"):
            raise ValueError(f"Invalid PagerDuty action: {action}")

        payload: dict[str, Any] = {
            "summary": summary,
            "severity": self._map_severity(severity),
            "source": source,
        }
        if component:
            payload["component"] = component
        if group:
            payload["group"] = group
        if details:
            payload["details"] = details
        if action == "resolve" and self._config.auto_resolve:
            payload["severity"] = "info"

        event: dict[str, Any] = {
            "routing_key": self.routing_key,
            "event_action": action,
            "payload": payload,
        }
        if incident_key:
            event["dedup_key"] = incident_key
        elif action == "trigger":
            event["dedup_key"] = str(uuid.uuid4())

        client = await self._get_client()
        try:
            resp = await client.post(
                "https://events.pagerduty.com/v2/enqueue",
                json=event,
            )
            resp.raise_for_status()
            data = resp.json()
            logger.info("PagerDuty alert sent: action=%s key=%s", action, data.get("dedup_key"))
            return data
        except httpx.HTTPError as exc:
            logger.error("PagerDuty alert failed: %s", exc)
            return None

    async def send_change_event(
        self,
        summary: str,
        source: str = "ipe",
        component: str = "",
        details: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        if not self.routing_key:
            logger.warning("PagerDuty routing key not configured; skipping change event")
            return None

        payload: dict[str, Any] = {
            "summary": summary,
            "source": source,
            "severity": "info",
        }
        if component:
            payload["component"] = component
        if details:
            payload["details"] = details

        event = {
            "routing_key": self.routing_key,
            "event_action": "change",
            "payload": payload,
        }

        client = await self._get_client()
        try:
            resp = await client.post(
                "https://events.pagerduty.com/v2/change/enqueue",
                json=event,
            )
            resp.raise_for_status()
            data = resp.json()
            logger.info("PagerDuty change event sent: %s", data.get("id", ""))
            return data
        except httpx.HTTPError as exc:
            logger.error("PagerDuty change event failed: %s", exc)
            return None