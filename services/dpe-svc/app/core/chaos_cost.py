"""Cost of Chaos aggregation (V6-R5).

Rolls up DelayEvent cost impacts and manual-override audit entries into
idle_time, rework, and expedite categories.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ipe_shared.models.audit_log import AuditLog
from ipe_shared.models.delay_event import DelayEvent
from ipe_shared.models.disruption import DisruptionEvent

CHAOS_CATEGORIES = {
    "idle_time": {
        "label": "Idle Time",
        "cause_categories": {
            "labor_absence",
            "capacity",
            "maintenance",
            "machine_breakdown",
            "operator_absence",
        },
        "audit_actions": {"schedule_override", "capacity_override"},
        "default_cost_per_minute": 2.5,
    },
    "rework": {
        "label": "Rework",
        "cause_categories": {"quality", "rework", "scrap", "defect"},
        "audit_actions": {"quality_override", "rework_logged"},
        "default_cost_per_minute": 3.75,
    },
    "expedite": {
        "label": "Expedite Freight",
        "cause_categories": {"supplier", "material", "expedite", "logistics", "shipping"},
        "audit_actions": {"expedite_po", "manual_expedite"},
        "default_cost_per_minute": 5.0,
    },
}

OVERRIDE_AUDIT_ACTIONS = {
    action for cfg in CHAOS_CATEGORIES.values() for action in cfg["audit_actions"]
}


def _category_for_cause(cause: str | None) -> str:
    normalized = (cause or "").lower()
    for code, cfg in CHAOS_CATEGORIES.items():
        if normalized in cfg["cause_categories"]:
            return code
    if "idle" in normalized or "wait" in normalized:
        return "idle_time"
    if "rework" in normalized or "quality" in normalized:
        return "rework"
    return "expedite"


def _category_for_audit_action(action: str) -> str:
    for code, cfg in CHAOS_CATEGORIES.items():
        if action in cfg["audit_actions"]:
            return code
    return "idle_time"


def _usd(value: float | Decimal | None) -> float:
    if value is None:
        return 0.0
    return round(float(value), 2)


async def aggregate_chaos_cost(
    session: AsyncSession,
    tenant_id: UUID,
    period_days: int = 7,
    category_filter: str | None = None,
) -> dict:
    """Aggregate chaos cost from delays and audit overrides for the period."""
    cutoff = datetime.now(UTC) - timedelta(days=period_days)
    category_totals = {code: 0.0 for code in CHAOS_CATEGORIES}
    mo_totals: dict[str, dict] = {}

    delay_stmt = (
        select(DelayEvent)
        .where(
            DelayEvent.tenant_id == tenant_id,
            DelayEvent.created_at >= cutoff,
        )
    )
    delay_rows = (await session.execute(delay_stmt)).scalars().all()

    for event in delay_rows:
        cat = _category_for_cause(event.cause_category)
        cfg = CHAOS_CATEGORIES[cat]
        if event.cost_impact is not None:
            usd = _usd(event.cost_impact)
        else:
            minutes = int(event.delay_minutes or 0)
            usd = round(minutes * cfg["default_cost_per_minute"], 2)
        category_totals[cat] += usd

        mo_key = str(event.mo_id)
        if mo_key not in mo_totals:
            mo_totals[mo_key] = {"chaos_usd": 0.0, "primary_category": cat}
        mo_totals[mo_key]["chaos_usd"] += usd
        if usd >= mo_totals[mo_key]["chaos_usd"] * 0.5:
            mo_totals[mo_key]["primary_category"] = cat

    audit_stmt = (
        select(AuditLog)
        .where(
            AuditLog.tenant_id == tenant_id,
            AuditLog.timestamp >= cutoff,
            AuditLog.action.in_(list(OVERRIDE_AUDIT_ACTIONS)),
        )
    )
    audit_rows = (await session.execute(audit_stmt)).scalars().all()

    for entry in audit_rows:
        cat = _category_for_audit_action(entry.action)
        after = entry.after_state or {}
        usd = _usd(after.get("cost_impact_usd") or after.get("chaos_cost_usd") or 500.0)
        category_totals[cat] += usd

    total = sum(category_totals.values())
    categories = []
    for code, cfg in CHAOS_CATEGORIES.items():
        usd = round(category_totals[code], 2)
        if category_filter and code != category_filter:
            continue
        pct = round((usd / total) * 100, 1) if total else 0.0
        categories.append({
            "code": code,
            "label": cfg["label"],
            "usd": usd,
            "pct": pct,
        })

    top_mos = sorted(
        [
            {
                "mo_id": mo_id,
                "chaos_usd": round(info["chaos_usd"], 2),
                "primary_category": info["primary_category"],
            }
            for mo_id, info in mo_totals.items()
            if info["chaos_usd"] > 0
        ],
        key=lambda x: x["chaos_usd"],
        reverse=True,
    )[:10]

    disruption_stmt = (
        select(DisruptionEvent)
        .where(
            DisruptionEvent.tenant_id == tenant_id,
            DisruptionEvent.detected_at >= cutoff,
            DisruptionEvent.resolved_at.is_(None),
        )
        .order_by(DisruptionEvent.detected_at.desc())
        .limit(5)
    )
    disruptions = (await session.execute(disruption_stmt)).scalars().all()
    war_room_links = []
    for d in disruptions:
        meta = d.event_metadata or {}
        chaos_usd = _usd(meta.get("total_cost_impact") or meta.get("cost_impact") or 0)
        if chaos_usd <= 0:
            chaos_usd = round(category_totals["expedite"] * 0.25, 2) or 1000.0
        war_room_links.append({
            "disruption_id": str(d.id),
            "chaos_usd": chaos_usd,
        })

    period_label = f"{period_days}d"
    return {
        "period": period_label,
        "total_chaos_usd": round(total, 2),
        "categories": categories,
        "top_mos": top_mos,
        "war_room_links": war_room_links,
    }
