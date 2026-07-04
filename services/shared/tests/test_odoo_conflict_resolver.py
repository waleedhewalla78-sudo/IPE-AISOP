"""Unit tests for Odoo conflict resolver."""

from datetime import UTC, datetime, timedelta

import pytest

from ipe_shared.events.odoo_conflict_resolver import (
    ConflictRecord,
    ConflictResolver,
    ConflictStrategy,
    _coerce_strategy,
)


def _record(
    *,
    ipe_version: int = 2,
    odoo_version: int = 3,
    ipe_updated_at: datetime | None = None,
    odoo_updated_at: datetime | None = None,
) -> ConflictRecord:
    now = datetime.now(UTC)
    return ConflictRecord(
        entity_type="manufacturing_order",
        entity_id="mo-1",
        ipe_version=ipe_version,
        ipe_updated_at=ipe_updated_at or now,
        odoo_version=odoo_version,
        odoo_updated_at=odoo_updated_at or (now - timedelta(minutes=5)),
        ipe_data={"planned_start": "2026-07-01T08:00:00Z"},
        odoo_data={"planned_start": "2026-07-01T09:00:00Z"},
    )


def test_detect_conflict_requires_version_and_timestamp_mismatch():
    resolver = ConflictResolver()
    now = datetime.now(UTC)
    assert resolver.detect_conflict("manufacturing_order", 2, now, 3, now - timedelta(minutes=1))
    assert not resolver.detect_conflict("manufacturing_order", 2, now, 2, now)
    assert not resolver.detect_conflict("manufacturing_order", 2, now, 3, now)


def test_resolve_ipe_wins():
    resolver = ConflictResolver({ "manufacturing_order": ConflictStrategy.IPE_WINS })
    conflict = _record()
    winner, data = resolver.resolve("manufacturing_order", conflict)
    assert winner == "ipe"
    assert data == conflict.ipe_data
    assert conflict.resolution == "ipe"


def test_resolve_odoo_wins_for_product():
    resolver = ConflictResolver()
    conflict = _record()
    conflict.entity_type = "product"
    winner, data = resolver.resolve("product", conflict)
    assert winner == "odoo"
    assert data == conflict.odoo_data


def test_resolve_last_write_wins_prefers_newer_ipe():
    resolver = ConflictResolver()
    now = datetime.now(UTC)
    conflict = _record(
        ipe_updated_at=now,
        odoo_updated_at=now - timedelta(hours=1),
    )
    winner, _ = resolver.resolve("manufacturing_order", conflict)
    assert winner == "ipe"


def test_resolve_manual_review():
    resolver = ConflictResolver({"manufacturing_order": ConflictStrategy.MANUAL_REVIEW})
    conflict = _record()
    winner, data = resolver.resolve("manufacturing_order", conflict)
    assert winner == "manual"
    assert "ipe" in data and "odoo" in data


def test_coerce_strategy_accepts_aliases():
    assert _coerce_strategy("lww") == ConflictStrategy.LAST_WRITE_WINS
    assert _coerce_strategy("odoo_wins") == ConflictStrategy.ODOO_WINS
