from __future__ import annotations

from collections import defaultdict
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select as sa_select
from sqlalchemy.ext.asyncio import AsyncSession

from ipe_shared.models.manufacturing_order import ManufacturingOrder
from ipe_shared.models.planning_intelligence import CapacityAlertConfig, CapacityUtilisation
from ipe_shared.models.work_center import WorkCenter
from ipe_shared.models.work_order import WorkOrder


DEFAULT_WEEKLY_CAPACITY_HOURS = 40.0
DEFAULT_OVERLOAD_THRESHOLD_PCT = 90.0


class UtilisationCalculator:
    @staticmethod
    def utilisation_pct(used: float | int | Decimal | None, available: float | int | Decimal | None) -> float:
        used_hours = float(used or 0)
        available_hours = float(available or 0)
        if available_hours <= 0:
            return 0.0
        return round((used_hours / available_hours) * 100.0, 2)

    @staticmethod
    def is_overload(pct: float | int | Decimal | None, threshold: float | int | Decimal | None) -> bool:
        return float(pct or 0) >= float(threshold or DEFAULT_OVERLOAD_THRESHOLD_PCT)

    @staticmethod
    def overload_hours(
        used: float | int | Decimal | None,
        available: float | int | Decimal | None,
    ) -> float:
        return round(max(0.0, float(used or 0) - float(available or 0)), 2)

    @staticmethod
    def period_start_for_week(value: date | None = None) -> date:
        current = value or datetime.now(UTC).date()
        return current - timedelta(days=current.weekday())

    @staticmethod
    def available_hours(work_center: WorkCenter) -> float:
        effective = getattr(work_center, "effective_capacity_hours", None)
        if effective is not None:
            return float(effective)

        per_day = getattr(work_center, "capacity_hours_per_day", None)
        if per_day is not None:
            return float(per_day) * 5.0

        return DEFAULT_WEEKLY_CAPACITY_HOURS

    @staticmethod
    def work_order_hours(work_order: WorkOrder) -> float:
        duration_mins = getattr(work_order, "duration_planned_mins", None)
        if duration_mins is not None:
            return float(duration_mins) / 60.0

        planned_start = getattr(work_order, "planned_start", None)
        planned_end = getattr(work_order, "planned_end", None)
        if planned_start and planned_end and planned_end > planned_start:
            return (planned_end - planned_start).total_seconds() / 3600.0

        return 0.0

    @staticmethod
    def manufacturing_order_hours(order: ManufacturingOrder) -> float:
        planned_start = getattr(order, "planned_start", None)
        planned_end = getattr(order, "planned_end", None)
        if planned_start and planned_end and planned_end > planned_start:
            return (planned_end - planned_start).total_seconds() / 3600.0
        return 0.0

    async def calculate(
        self,
        session: AsyncSession,
        tenant_id: UUID,
        *,
        period_start: date | None = None,
        period_type: str = "week",
    ) -> list[CapacityUtilisation]:
        start = period_start or self.period_start_for_week()

        config = await self._get_config(session, tenant_id)
        threshold = float(config.overload_threshold_pct) if config else DEFAULT_OVERLOAD_THRESHOLD_PCT

        work_centers = (
            await session.execute(sa_select(WorkCenter).where(WorkCenter.tenant_id == tenant_id))
        ).scalars().all()

        work_orders = (
            await session.execute(
                sa_select(WorkOrder).where(
                    WorkOrder.tenant_id == tenant_id,
                    WorkOrder.status.notin_(["completed", "cancelled"]),
                )
            )
        ).scalars().all()

        used_by_wc: dict[UUID, float] = defaultdict(float)
        for work_order in work_orders:
            if work_order.work_center_id:
                used_by_wc[work_order.work_center_id] += self.work_order_hours(work_order)

        rows: list[CapacityUtilisation] = []
        for work_center in work_centers:
            available = round(self.available_hours(work_center), 2)
            used = round(used_by_wc.get(work_center.id, 0.0), 2)
            pct = self.utilisation_pct(used, available)
            overload = self.is_overload(pct, threshold)
            overload_hrs = self.overload_hours(used, available)

            existing = (
                await session.execute(
                    sa_select(CapacityUtilisation).where(
                        CapacityUtilisation.tenant_id == tenant_id,
                        CapacityUtilisation.work_center_id == work_center.id,
                        CapacityUtilisation.period_start == start,
                        CapacityUtilisation.period_type == period_type,
                    )
                )
            ).scalar_one_or_none()

            row = existing or CapacityUtilisation(
                tenant_id=tenant_id,
                work_center_id=work_center.id,
                period_start=start,
                period_type=period_type,
            )
            row.capacity_available_hours = available
            row.capacity_used_hours = used
            row.utilisation_pct = pct
            row.overload = overload
            row.overload_hours = overload_hrs
            row.calculated_at = datetime.now(UTC)

            if existing is None:
                session.add(row)
            rows.append(row)

        await session.commit()
        return rows

    async def _get_config(self, session: AsyncSession, tenant_id: UUID) -> CapacityAlertConfig | None:
        return (
            await session.execute(
                sa_select(CapacityAlertConfig).where(CapacityAlertConfig.tenant_id == tenant_id)
            )
        ).scalar_one_or_none()
