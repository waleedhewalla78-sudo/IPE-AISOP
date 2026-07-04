"""
Resolves conflicts when IPE and Odoo modify the same entity concurrently.
Strategy: Last-Write-Wins with version tracking, configurable per entity type.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

from ipe_shared.config import settings


class ConflictStrategy(Enum):
    IPE_WINS = "ipe_wins"
    ODOO_WINS = "odoo_wins"
    LAST_WRITE_WINS = "lww"
    MANUAL_REVIEW = "manual"


DEFAULT_STRATEGIES: dict[str, ConflictStrategy] = {
    "manufacturing_order": ConflictStrategy.LAST_WRITE_WINS,
    "product": ConflictStrategy.ODOO_WINS,
    "bom": ConflictStrategy.ODOO_WINS,
    "inventory": ConflictStrategy.LAST_WRITE_WINS,
    "routing": ConflictStrategy.ODOO_WINS,
}


def _coerce_strategy(value: str | ConflictStrategy) -> ConflictStrategy:
    if isinstance(value, ConflictStrategy):
        return value
    normalized = str(value).strip().lower()
    for strategy in ConflictStrategy:
        if strategy.value == normalized or strategy.name.lower() == normalized:
            return strategy
    raise ValueError(f"Unknown conflict strategy: {value}")


def load_strategy_overrides(path: str | Path | None = None) -> dict[str, ConflictStrategy]:
    configured = path or getattr(settings, "ODOO_CONFLICT_STRATEGIES", "") or os.getenv(
        "IPE_ODOO_CONFLICT_STRATEGIES", "config/odoo-conflict-strategies.json"
    )
    try:
        with Path(configured).open(encoding="utf-8") as handle:
            raw = json.load(handle)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}
    if not isinstance(raw, dict):
        return {}
    return {entity: _coerce_strategy(strategy) for entity, strategy in raw.items()}


@dataclass
class ConflictRecord:
    entity_type: str
    entity_id: str
    ipe_version: int
    ipe_updated_at: datetime
    odoo_version: int
    odoo_updated_at: datetime
    ipe_data: dict[str, Any]
    odoo_data: dict[str, Any]
    resolution: str | None = None
    resolved_at: datetime | None = None
    resolved_by: str | None = None
    merged_data: dict[str, Any] = field(default_factory=dict)


class ConflictResolver:
    """Detect and resolve IPE-Odoo conflicts."""

    def __init__(self, strategy_overrides: dict[str, ConflictStrategy] | None = None):
        self.strategies = {**DEFAULT_STRATEGIES, **(strategy_overrides or {})}

    def detect_conflict(
        self,
        entity_type: str,
        ipe_version: int,
        ipe_updated_at: datetime,
        odoo_version: int,
        odoo_updated_at: datetime,
    ) -> bool:
        """Return True if a conflict exists (both sides modified since last sync)."""
        _ = entity_type
        return ipe_version != odoo_version and ipe_updated_at != odoo_updated_at

    def resolve(
        self,
        entity_type: str,
        conflict: ConflictRecord,
    ) -> tuple[str, dict[str, Any]]:
        """
        Resolve a conflict. Returns (winner, merged_data).
        winner is "ipe", "odoo", or "manual".
        """
        strategy = self.strategies.get(entity_type, ConflictStrategy.LAST_WRITE_WINS)

        if strategy == ConflictStrategy.IPE_WINS:
            winner, merged = "ipe", conflict.ipe_data
        elif strategy == ConflictStrategy.ODOO_WINS:
            winner, merged = "odoo", conflict.odoo_data
        elif strategy == ConflictStrategy.LAST_WRITE_WINS:
            ipe_at = _as_utc(conflict.ipe_updated_at)
            odoo_at = _as_utc(conflict.odoo_updated_at)
            if ipe_at > odoo_at:
                winner, merged = "ipe", conflict.ipe_data
            else:
                winner, merged = "odoo", conflict.odoo_data
        else:
            winner, merged = "manual", {
                "ipe": conflict.ipe_data,
                "odoo": conflict.odoo_data,
                "ipe_updated_at": _as_utc(conflict.ipe_updated_at).isoformat(),
                "odoo_updated_at": _as_utc(conflict.odoo_updated_at).isoformat(),
            }

        conflict.resolution = winner
        conflict.merged_data = merged
        conflict.resolved_at = datetime.now(UTC)
        return winner, merged


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


odoo_conflict_resolver = ConflictResolver(load_strategy_overrides())
