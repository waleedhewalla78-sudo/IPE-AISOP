from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

import httpx

from ipe_shared.config import settings

logger = logging.getLogger(__name__)


@dataclass
class AlertManagerConfig:
    base_url: str = ""
    timeout: float = 10.0


class AlertManagerClient:
    def __init__(self, config: AlertManagerConfig | None = None):
        self._config = config or AlertManagerConfig()
        self._client: httpx.AsyncClient | None = None

    @property
    def base_url(self) -> str:
        return self._config.base_url or settings.ALERTMANAGER_URL

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=self._config.timeout,
                base_url=self.base_url or "http://localhost:9093",
            )
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def send_alert(
        self,
        name: str,
        severity: str = "warning",
        source: str = "ipe",
        labels: dict[str, str] | None = None,
        annotations: dict[str, str] | None = None,
        starts_at: str | None = None,
        generator_url: str = "",
    ) -> bool:
        if not self.base_url:
            logger.warning("Alertmanager URL not configured; skipping alert")
            return False

        alert_labels: dict[str, str] = {
            "alertname": name,
            "severity": severity,
            "source": source,
        }
        if labels:
            alert_labels.update(labels)

        alert_annotations: dict[str, str] = {}
        if annotations:
            alert_annotations.update(annotations)

        payload: list[dict[str, Any]] = [
            {
                "labels": alert_labels,
                "annotations": alert_annotations,
                "startsAt": starts_at or datetime.now(UTC).isoformat(),
                "generatorURL": generator_url or "",
            }
        ]

        client = await self._get_client()
        try:
            resp = await client.post("/api/v2/alerts", json=payload)
            resp.raise_for_status()
            logger.info("Alertmanager alert sent: %s", name)
            return True
        except httpx.HTTPError as exc:
            logger.error("Alertmanager alert failed: %s", exc)
            return False

    async def resolve_alert(
        self,
        name: str,
        source: str = "ipe",
        labels: dict[str, str] | None = None,
        ends_at: str | None = None,
    ) -> bool:
        if not self.base_url:
            logger.warning("Alertmanager URL not configured; skipping resolve")
            return False

        alert_labels: dict[str, str] = {
            "alertname": name,
            "source": source,
        }
        if labels:
            alert_labels.update(labels)

        payload: list[dict[str, Any]] = [
            {
                "labels": alert_labels,
                "annotations": {},
                "startsAt": datetime.now(UTC).isoformat(),
                "endsAt": ends_at or datetime.now(UTC).isoformat(),
                "generatorURL": "",
            }
        ]

        client = await self._get_client()
        try:
            resp = await client.post("/api/v2/alerts", json=payload)
            resp.raise_for_status()
            logger.info("Alertmanager alert resolved: %s", name)
            return True
        except httpx.HTTPError as exc:
            logger.error("Alertmanager resolve failed: %s", exc)
            return False

    async def list_alerts(
        self,
        filters: list[str] | None = None,
        receiver: str | None = None,
        silenced: bool | None = None,
        inhibited: bool | None = None,
    ) -> list[dict[str, Any]]:
        if not self.base_url:
            logger.warning("Alertmanager URL not configured; returning empty list")
            return []

        params: dict[str, Any] = {}
        if filters:
            params["filter"] = filters
        if receiver is not None:
            params["receiver"] = receiver
        if silenced is not None:
            params["silenced"] = str(silenced).lower()
        if inhibited is not None:
            params["inhibited"] = str(inhibited).lower()

        client = await self._get_client()
        try:
            resp = await client.get("/api/v2/alerts", params=params)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as exc:
            logger.error("Alertmanager list_alerts failed: %s", exc)
            return []