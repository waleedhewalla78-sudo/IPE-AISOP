"""OTD aggregator service layer (W1-06 Sprint 4).

Wraps existing aggregation helpers and adds snapshot capture / historical backfill.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import and_, extract, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.chaos_cost import aggregate_chaos_cost
from app.core.otd_aggregation import (
    compute_baseline_comparison,
    compute_otd_kpis,
    compute_otd_trend,
    compute_root_cause,
    upsert_daily_snapshot,
)
from ipe_shared.models import ManufacturingOrder
from ipe_shared.models.otd_snapshot import OtdSnapshot


class OTDAggregator:
    """Daily OTD snapshot capture, trends, root causes, and cost-of-chaos."""

    async def capture_daily_snapshot(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        snapshot_date: date | None = None,
        *,
        daily_penalty_rate: float = 500.0,
    ) -> dict[str, Any]:
        """Calculate OTD for MOs completed on snapshot_date and upsert snapshot."""
        target = snapshot_date or datetime.now(UTC).date()
        day_start = datetime(target.year, target.month, target.day, tzinfo=UTC)
        day_end = day_start + timedelta(days=1)

        stmt = select(
            func.count().label("total"),
            func.count()
            .filter(ManufacturingOrder.actual_end <= ManufacturingOrder.planned_end)
            .label("on_time"),
            func.avg(
                extract("epoch", ManufacturingOrder.actual_end - ManufacturingOrder.planned_end)
                / 86400.0
            )
            .filter(ManufacturingOrder.actual_end > ManufacturingOrder.planned_end)
            .label("avg_delay"),
            func.max(
                extract("epoch", ManufacturingOrder.actual_end - ManufacturingOrder.planned_end)
                / 86400.0
            )
            .filter(ManufacturingOrder.actual_end > ManufacturingOrder.planned_end)
            .label("max_delay"),
        ).where(
            ManufacturingOrder.tenant_id == tenant_id,
            ManufacturingOrder.actual_end.isnot(None),
            ManufacturingOrder.planned_end.isnot(None),
            ManufacturingOrder.actual_end >= day_start,
            ManufacturingOrder.actual_end < day_end,
        )
        row = (await db.execute(stmt)).one()
        total = int(row.total or 0)
        on_time = int(row.on_time or 0)
        late = max(0, total - on_time)
        otd_pct = round((on_time / total) * 100, 2) if total else None
        avg_delay = round(float(row.avg_delay), 2) if row.avg_delay is not None else None
        max_delay = int(float(row.max_delay)) if row.max_delay is not None else None
        cost_of_delay = round(late * (avg_delay or 0) * daily_penalty_rate, 2) if late else 0.0

        snapshot = await upsert_daily_snapshot(db, tenant_id, target)
        snapshot.otd_pct = otd_pct
        snapshot.completed_mos = total
        snapshot.on_time_mos = on_time
        snapshot.avg_delay_days = avg_delay
        snapshot.chaos_cost_usd = cost_of_delay
        if hasattr(snapshot, "metadata_json") and isinstance(snapshot.metadata_json, dict):
            meta = dict(snapshot.metadata_json)
            meta.update({"late_count": late, "max_delay_days": max_delay, "cost_of_delay": cost_of_delay})
            snapshot.metadata_json = meta
        await db.commit()

        return {
            "snapshot_date": target.isoformat(),
            "otd_pct": otd_pct,
            "total": total,
            "on_time": on_time,
            "late": late,
            "avg_delay_days": avg_delay,
            "max_delay_days": max_delay,
            "cost_of_delay": cost_of_delay,
        }

    async def capture_historical(
        self, db: AsyncSession, tenant_id: UUID, months_back: int = 6
    ) -> dict[str, Any]:
        """Backfill weekly OTD snapshots for the lookback window."""
        months_back = max(1, min(24, int(months_back)))
        end = datetime.now(UTC).date()
        start = end - timedelta(days=months_back * 30)
        # Align to Mondays
        cursor = start - timedelta(days=start.weekday())
        created = 0
        while cursor <= end:
            week_end = cursor + timedelta(days=7)
            stmt = select(
                func.count().label("total"),
                func.count()
                .filter(ManufacturingOrder.actual_end <= ManufacturingOrder.planned_end)
                .label("on_time"),
            ).where(
                ManufacturingOrder.tenant_id == tenant_id,
                ManufacturingOrder.actual_end.isnot(None),
                ManufacturingOrder.planned_end.isnot(None),
                ManufacturingOrder.actual_end >= datetime(cursor.year, cursor.month, cursor.day, tzinfo=UTC),
                ManufacturingOrder.actual_end
                < datetime(week_end.year, week_end.month, week_end.day, tzinfo=UTC),
            )
            row = (await db.execute(stmt)).one()
            total = int(row.total or 0)
            on_time = int(row.on_time or 0)
            otd_pct = round((on_time / total) * 100, 1) if total else None

            existing = (
                await db.execute(
                    select(OtdSnapshot).where(
                        and_(
                            OtdSnapshot.tenant_id == tenant_id,
                            OtdSnapshot.snapshot_date == cursor,
                            OtdSnapshot.period == "weekly",
                            OtdSnapshot.supplier_id.is_(None),
                            OtdSnapshot.work_center_id.is_(None),
                            OtdSnapshot.plant_id.is_(None),
                        )
                    )
                )
            ).scalar_one_or_none()
            if existing:
                existing.otd_pct = otd_pct
                existing.completed_mos = total
                existing.on_time_mos = on_time
            else:
                db.add(
                    OtdSnapshot(
                        tenant_id=tenant_id,
                        snapshot_date=cursor,
                        period="weekly",
                        otd_pct=otd_pct,
                        completed_mos=total,
                        on_time_mos=on_time,
                        orders_at_risk=0,
                        chaos_cost_usd=Decimal("0"),
                    )
                )
                created += 1
            cursor = week_end

        await db.commit()
        return {"snapshots_created": created, "months_back": months_back}

    async def get_trend(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        period: str = "daily",
        range_days: int = 90,
    ) -> list[dict[str, Any]]:
        points = await compute_otd_trend(
            db, tenant_id, period=period, range_param=f"{range_days}d"
        )
        return [
            {
                "date": p.get("period_start"),
                "otd_pct": p.get("otd_pct"),
                "total": p.get("completed_mos", 0),
                "on_time": p.get("on_time_mos", 0),
                "late": max(0, int(p.get("completed_mos") or 0) - int(p.get("on_time_mos") or 0)),
            }
            for p in points
        ]

    async def get_root_causes(
        self, db: AsyncSession, tenant_id: UUID, range_days: int = 30
    ) -> list[dict[str, Any]]:
        causes = await compute_root_cause(db, tenant_id, range_param=f"{range_days}d")
        if causes:
            return [
                {
                    "category": c.get("cause_category") or "other",
                    "count": c.get("count", 0),
                    "pct": c.get("pct", 0),
                    "avg_delay_days": None,
                    "total_cost": c.get("cost_usd", 0),
                }
                for c in causes
            ]

        # Fallback: late vs on-time from completed MOs
        kpis = await compute_otd_kpis(db, tenant_id, lookback_days=range_days)
        total = int(kpis.get("completed_mos") or 0)
        on_time = int(kpis.get("on_time_mos") or 0)
        late = max(0, total - on_time)
        if late == 0:
            return []
        return [
            {
                "category": "late",
                "count": late,
                "pct": round(late * 100.0 / total, 1) if total else 0,
                "avg_delay_days": kpis.get("avg_delay_days"),
                "total_cost": kpis.get("chaos_cost_usd", 0),
            }
        ]

    async def get_cost_of_chaos(
        self, db: AsyncSession, tenant_id: UUID, range_days: int = 30
    ) -> dict[str, Any]:
        data = await aggregate_chaos_cost(db, tenant_id, period_days=range_days)
        total = float(data.get("total_chaos_usd") or 0)
        categories = data.get("categories") or []
        return {
            "total_cost": total,
            "currency": "EGP",
            "by_category": [
                {
                    "category": c.get("code") or c.get("label") or "other",
                    "cost": c.get("usd", 0),
                    "count": c.get("count"),
                }
                for c in categories
            ],
            "daily_avg": round(total / max(range_days, 1), 2),
            "trend": data.get("trend") or [],
        }

    async def get_summary(self, db: AsyncSession, tenant_id: UUID) -> dict[str, Any]:
        current = await compute_otd_kpis(db, tenant_id, lookback_days=30)
        prior = await compute_otd_kpis(db, tenant_id, lookback_days=60)
        baseline = await compute_baseline_comparison(db, tenant_id, lookback_days=30)
        current_otd = current.get("otd_pct")
        # Approximate prior-period OTD as mid-window: not exact but stable for dashboard
        prior_otd = prior.get("otd_pct")
        improvement = baseline.get("improvement_pct")
        direction = "stable"
        if current_otd is not None and prior_otd is not None:
            if current_otd > prior_otd:
                direction = "improving"
            elif current_otd < prior_otd:
                direction = "declining"
        late = max(0, int(current.get("completed_mos") or 0) - int(current.get("on_time_mos") or 0))
        return {
            "current_period_otd": current_otd,
            "prior_period_otd": prior_otd,
            "trend_direction": direction,
            "improvement_vs_baseline": improvement,
            "total_late_this_month": late,
            "worst_delay_days": current.get("avg_delay_days"),
            "total_cost_this_month": current.get("chaos_cost_usd", 0),
            "baseline_otd_pct": (baseline.get("baseline") or {}).get("otd_pct")
            if isinstance(baseline.get("baseline"), dict)
            else None,
        }


# Module-level singleton for API routes
otd_aggregator = OTDAggregator()
