"""CAPA tracking for Quality Intelligence (A10)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4


_CAPA_STORE: list[dict[str, Any]] = []


def create_capa(
    *,
    mo_id: str,
    defect_type: str,
    root_cause: str | None = None,
    severity: str = "medium",
    owner: str = "quality_manager",
) -> dict[str, Any]:
    now = datetime.now(UTC)
    capa = {
        "capa_id": f"CAPA-{uuid4().hex[:8].upper()}",
        "mo_id": mo_id,
        "defect_type": defect_type,
        "root_cause": root_cause or "pending_analysis",
        "severity": severity,
        "owner": owner,
        "status": "open",
        "created_at": now.isoformat(),
        "verify_windows": {
            "d30": (now + timedelta(days=30)).date().isoformat(),
            "d60": (now + timedelta(days=60)).date().isoformat(),
            "d90": (now + timedelta(days=90)).date().isoformat(),
        },
        "agent_id": "A10",
    }
    _CAPA_STORE.append(capa)
    return capa


def list_capas(*, status: str | None = None) -> list[dict[str, Any]]:
    if status:
        return [c for c in _CAPA_STORE if c["status"] == status]
    return list(_CAPA_STORE)


def clear_capa_store() -> None:
    _CAPA_STORE.clear()
