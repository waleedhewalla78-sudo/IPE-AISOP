"""OTD KPI aggregation with dimensional filters (W1-07 / Sprint S6)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import and_, extract, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.chaos_cost import aggregate_chaos_cost
from ipe_shared.models import DelayEvent, ManufacturingOrder, SupplyOrder, Tenant, WorkCenter, WorkOrder
from ipe_shared.models.otd_snapshot import OtdSnapshot


def _parse_range_days(range_param: str) -> int:
    normalized = (range_param or "30d").lower().strip()
    if normalized.endswith("d"):
        try:
            return max(1, min(365, int(normalized[:-1])))
        except ValueError:
            return 30
    return 30


def _period_trunc(period: str):
    if period == "weekly":
        return func.date_trunc("week", ManufacturingOrder.actual_end)
    if period == "monthly":
        return func.date_trunc("month", ManufacturingOrder.actual_end)
    return func.date_trunc("day", ManufacturingOrder.actual_end)


async def _filtered_mo_ids(
    session: AsyncSession,
    tenant_id: UUID,
    supplier_id: UUID | None,
    line_id: UUID | None,
    region_id: UUID | None,
) -> set[UUID] | None:
    """Return MO id set when dimensional filters apply; None means no filter."""
    if not any([supplier_id, line_id, region_id]):
        return None

    mo_ids: set[UUID] = set()

    if line_id or region_id:
        stmt = (
            select(WorkOrder.mo_id)
            .join(WorkCenter, WorkCenter.id == WorkOrder.work_center_id)
            .where(WorkOrder.tenant_id == tenant_id)
        )
        if line_id:
            stmt = stmt.where(WorkOrder.work_center_id == line_id)
        if region_id:
            stmt = stmt.where(WorkCenter.plant_id == region_id)
        rows = (await session.execute(stmt)).fetchall()
        mo_ids.update(row[0] for row in rows)

    if supplier_id:
        supplier_stmt = (
            select(DelayEvent.mo_id)
            .join(SupplyOrder, SupplyOrder.id == DelayEvent.linked_po_id)
            .where(
                DelayEvent.tenant_id == tenant_id,
                SupplyOrder.supplier_id == supplier_id,
            )
        )
        supplier_rows = (await session.execute(supplier_stmt)).fetchall()
        supplier_mos = {row[0] for row in supplier_rows}
        if line_id or region_id:
            mo_ids &= supplier_mos
        else:
            mo_ids = supplier_mos

    return mo_ids


def _mo_filter_clause(mo_ids: set[UUID] | None):
    if mo_ids is None:
        return True
    if not mo_ids:
        return ManufacturingOrder.id.is_(None)
    return ManufacturingOrder.id.in_(mo_ids)


async def compute_otd_kpis(
    session: AsyncSession,
    tenant_id: UUID,
    lookback_days: int = 30,
    supplier_id: UUID | None = None,
    line_id: UUID | None = None,
    region_id: UUID | None = None,
) -> dict:
    """Aggregate five OTD KPIs for dashboard cards."""
    cutoff = datetime.now(UTC) - timedelta(days=lookback_days)
    mo_ids = await _filtered_mo_ids(session, tenant_id, supplier_id, line_id, region_id)

    base_where = and_(
        ManufacturingOrder.tenant_id == tenant_id,
        _mo_filter_clause(mo_ids),
    )

    completed_stmt = select(
        func.count().filter(
            ManufacturingOrder.actual_end <= ManufacturingOrder.planned_end,
        ).label("on_time"),
        func.count().label("total"),
    ).where(
        base_where,
        ManufacturingOrder.actual_end.isnot(None),
        ManufacturingOrder.planned_end.isnot(None),
        ManufacturingOrder.actual_end >= cutoff,
    )
    completed_row = (await session.execute(completed_stmt)).one()
    total = int(completed_row.total or 0)
    on_time = int(completed_row.on_time or 0)
    otd_pct = round((on_time / total) * 100, 1) if total else None

    risk_stmt = select(func.count()).where(
        base_where,
        or_(
            ManufacturingOrder.feasibility_score < 70,
            and_(
                ManufacturingOrder.planned_end.isnot(None),
                ManufacturingOrder.planned_end < datetime.now(UTC),
                ManufacturingOrder.status.notin_(["completed", "cancelled"]),
            ),
        ),
    )
    orders_at_risk = int((await session.execute(risk_stmt)).scalar() or 0)

    delay_expr = extract("epoch", ManufacturingOrder.actual_end - ManufacturingOrder.planned_end) / 86400.0
    delay_stmt = select(func.avg(delay_expr)).where(
        base_where,
        ManufacturingOrder.actual_end.isnot(None),
        ManufacturingOrder.planned_end.isnot(None),
        ManufacturingOrder.actual_end > ManufacturingOrder.planned_end,
        ManufacturingOrder.actual_end >= cutoff,
    )
    avg_delay = (await session.execute(delay_stmt)).scalar()
    avg_delay_days = round(float(avg_delay), 1) if avg_delay is not None else None

    chaos = await aggregate_chaos_cost(session, tenant_id, period_days=lookback_days)
    chaos_cost_usd = chaos.get("total_chaos_usd", 0.0)

    return {
        "otd_pct": otd_pct,
        "completed_mos": total,
        "on_time_mos": on_time,
        "orders_at_risk": orders_at_risk,
        "avg_delay_days": avg_delay_days,
        "chaos_cost_usd": chaos_cost_usd,
        "lookback_days": lookback_days,
        "filters": {
            "supplier_id": str(supplier_id) if supplier_id else None,
            "line_id": str(line_id) if line_id else None,
            "region_id": str(region_id) if region_id else None,
        },
    }


async def compute_otd_trend(
    session: AsyncSession,
    tenant_id: UUID,
    period: str = "daily",
    range_param: str = "30d",
    supplier_id: UUID | None = None,
    line_id: UUID | None = None,
    region_id: UUID | None = None,
) -> list[dict]:
    """OTD % per period bucket."""
    lookback_days = _parse_range_days(range_param)
    cutoff = datetime.now(UTC) - timedelta(days=lookback_days)
    mo_ids = await _filtered_mo_ids(session, tenant_id, supplier_id, line_id, region_id)
    bucket = _period_trunc(period)

    stmt = (
        select(
            bucket.label("period_start"),
            func.count().label("total"),
            func.count().filter(
                ManufacturingOrder.actual_end <= ManufacturingOrder.planned_end,
            ).label("on_time"),
        )
        .where(
            ManufacturingOrder.tenant_id == tenant_id,
            _mo_filter_clause(mo_ids),
            ManufacturingOrder.actual_end.isnot(None),
            ManufacturingOrder.planned_end.isnot(None),
            ManufacturingOrder.actual_end >= cutoff,
        )
        .group_by(bucket)
        .order_by(bucket)
    )
    rows = (await session.execute(stmt)).fetchall()
    return [
        {
            "period_start": str(row.period_start.date()) if row.period_start else None,
            "otd_pct": round((int(row.on_time) / int(row.total)) * 100, 1) if row.total else None,
            "completed_mos": int(row.total or 0),
            "on_time_mos": int(row.on_time or 0),
        }
        for row in rows
    ]


async def compute_root_cause(
    session: AsyncSession,
    tenant_id: UUID,
    range_param: str = "30d",
    supplier_id: UUID | None = None,
    line_id: UUID | None = None,
    region_id: UUID | None = None,
) -> list[dict]:
    """Delay breakdown by cause category."""
    lookback_days = _parse_range_days(range_param)
    cutoff = datetime.now(UTC) - timedelta(days=lookback_days)
    mo_ids = await _filtered_mo_ids(session, tenant_id, supplier_id, line_id, region_id)

    base_where = [DelayEvent.tenant_id == tenant_id, DelayEvent.created_at >= cutoff]
    if mo_ids is not None:
        if not mo_ids:
            return []
        base_where.append(DelayEvent.mo_id.in_(mo_ids))
    if supplier_id:
        base_where.append(
            DelayEvent.linked_po_id.in_(
                select(SupplyOrder.id).where(
                    SupplyOrder.tenant_id == tenant_id,
                    SupplyOrder.supplier_id == supplier_id,
                )
            )
        )
    if line_id:
        base_where.append(DelayEvent.linked_wc_id == line_id)

    total_stmt = select(func.count()).select_from(DelayEvent).where(*base_where)
    total_count = int((await session.execute(total_stmt)).scalar() or 0)
    if total_count == 0:
        return []

    stmt = (
        select(
            DelayEvent.cause_category,
            func.count().label("cnt"),
            func.coalesce(func.sum(DelayEvent.cost_impact), 0).label("cost_usd"),
        )
        .where(*base_where)
        .group_by(DelayEvent.cause_category)
        .order_by(func.count().desc())
    )
    rows = (await session.execute(stmt)).fetchall()
    return [
        {
            "cause_category": row.cause_category,
            "count": int(row.cnt),
            "pct": round(int(row.cnt) * 100.0 / total_count, 1),
            "cost_usd": round(float(row.cost_usd or 0), 2),
        }
        for row in rows
    ]


async def compute_baseline_comparison(
    session: AsyncSession,
    tenant_id: UUID,
    lookback_days: int = 30,
) -> dict:
    """Pre/post IPE baseline vs current OTD."""
    tenant = (await session.execute(select(Tenant).where(Tenant.id == tenant_id))).scalar_one_or_none()
    baseline = (tenant.config or {}).get("otd_baseline") if tenant else None
    current = await compute_otd_kpis(session, tenant_id, lookback_days=lookback_days)
    delta = None
    if baseline and baseline.get("otd_pct") is not None and current.get("otd_pct") is not None:
        delta = round(current["otd_pct"] - float(baseline["otd_pct"]), 1)

    return {
        "baseline": baseline,
        "current": current,
        "delta_vs_baseline": delta,
        "improvement_pct": delta,
    }


async def upsert_daily_snapshot(
    session: AsyncSession,
    tenant_id: UUID,
    snapshot_date,
    supplier_id: UUID | None = None,
    line_id: UUID | None = None,
    region_id: UUID | None = None,
) -> OtdSnapshot:
    """Persist a daily OTD snapshot row (aggregation consumer hook)."""
    kpis = await compute_otd_kpis(
        session,
        tenant_id,
        lookback_days=1,
        supplier_id=supplier_id,
        line_id=line_id,
        region_id=region_id,
    )
    existing = (
        await session.execute(
            select(OtdSnapshot).where(
                OtdSnapshot.tenant_id == tenant_id,
                OtdSnapshot.snapshot_date == snapshot_date,
                OtdSnapshot.period == "daily",
                OtdSnapshot.supplier_id == supplier_id,
                OtdSnapshot.work_center_id == line_id,
                OtdSnapshot.plant_id == region_id,
            )
        )
    ).scalar_one_or_none()

    if existing:
        existing.otd_pct = kpis["otd_pct"]
        existing.completed_mos = kpis["completed_mos"]
        existing.on_time_mos = kpis["on_time_mos"]
        existing.orders_at_risk = kpis["orders_at_risk"]
        existing.avg_delay_days = kpis["avg_delay_days"]
        existing.chaos_cost_usd = kpis["chaos_cost_usd"]
        return existing

    row = OtdSnapshot(
        tenant_id=tenant_id,
        snapshot_date=snapshot_date,
        period="daily",
        supplier_id=supplier_id,
        work_center_id=line_id,
        plant_id=region_id,
        otd_pct=kpis["otd_pct"],
        completed_mos=kpis["completed_mos"],
        on_time_mos=kpis["on_time_mos"],
        orders_at_risk=kpis["orders_at_risk"],
        avg_delay_days=kpis["avg_delay_days"],
        chaos_cost_usd=kpis["chaos_cost_usd"],
    )
    session.add(row)
    return row
