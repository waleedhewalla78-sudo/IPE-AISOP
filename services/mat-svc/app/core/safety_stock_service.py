"""Safety stock API service layer."""
from __future__ import annotations

from collections import defaultdict
from datetime import UTC, date, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.safety_stock import calculate_safety_stock_ibp
from ipe_shared.models.demand import DemandLine
from ipe_shared.models.inventory import InventoryPosition
from ipe_shared.models.planning_intelligence import (
    LeadTimeHistory,
    ProductSegment,
    SafetyStockRecord,
)
from ipe_shared.models.product import Product


def _sample_std(values: list[float]) -> float:
    if len(values) <= 1:
        return 0.0
    mean = sum(values) / len(values)
    variance = sum((value - mean) ** 2 for value in values) / (len(values) - 1)
    return variance**0.5


def _weekly_buckets(lines: list[DemandLine]) -> list[float]:
    buckets: dict[tuple[int, int], float] = defaultdict(float)
    for line in lines:
        iso_year, iso_week, _ = line.required_date.date().isocalendar()
        buckets[(iso_year, iso_week)] += float(line.quantity or 0)
    return [buckets[key] for key in sorted(buckets)]


def _product_unit_cost(product: Product) -> float:
    for attr in ("unit_cost", "standard_cost"):
        value = getattr(product, attr, None)
        if value is not None:
            return float(value or 0)
    return 0.0


class SafetyStockService:
    """Calculates and persists material safety stock records."""

    async def calculate_all(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        product_id: UUID | None = None,
        service_level_pct: float | None = None,
        period_days: int = 7,
        history_days: int = 365,
    ) -> dict:
        product_stmt = select(Product).where(Product.tenant_id == tenant_id)
        if product_id:
            product_stmt = product_stmt.where(Product.id == product_id)
        products = (await db.execute(product_stmt)).scalars().all()

        cutoff = datetime.now(UTC) - timedelta(days=history_days)
        demand_stmt = (
            select(DemandLine)
            .where(DemandLine.tenant_id == tenant_id)
            .where(DemandLine.required_date >= cutoff)
        )
        if product_id:
            demand_stmt = demand_stmt.where(DemandLine.product_id == product_id)
        demand_lines = (await db.execute(demand_stmt)).scalars().all()

        lead_time_stmt = select(LeadTimeHistory).where(LeadTimeHistory.tenant_id == tenant_id)
        if product_id:
            lead_time_stmt = lead_time_stmt.where(LeadTimeHistory.product_id == product_id)
        lead_time_rows = (await db.execute(lead_time_stmt)).scalars().all()

        latest_segment_date = (
            await db.execute(
                select(func.max(ProductSegment.segmentation_date)).where(
                    ProductSegment.tenant_id == tenant_id
                )
            )
        ).scalar_one_or_none()
        segment_rows = []
        if latest_segment_date:
            segment_stmt = select(ProductSegment).where(
                ProductSegment.tenant_id == tenant_id,
                ProductSegment.segmentation_date == latest_segment_date,
            )
            if product_id:
                segment_stmt = segment_stmt.where(ProductSegment.product_id == product_id)
            segment_rows = (await db.execute(segment_stmt)).scalars().all()

        inventory_rows = (
            await db.execute(
                select(
                    InventoryPosition.product_id,
                    func.coalesce(func.sum(InventoryPosition.qty_on_hand), 0).label("qty_on_hand"),
                )
                .where(InventoryPosition.tenant_id == tenant_id)
                .group_by(InventoryPosition.product_id)
            )
        ).all()

        demand_by_product: dict[UUID, list[DemandLine]] = defaultdict(list)
        for line in demand_lines:
            demand_by_product[line.product_id].append(line)

        lead_times_by_product: dict[UUID, list[float]] = defaultdict(list)
        for row in lead_time_rows:
            if row.lead_time_days is not None:
                lead_times_by_product[row.product_id].append(float(row.lead_time_days))

        segments_by_product = {row.product_id: row for row in segment_rows}
        inventory_by_product = {
            row.product_id: float(row.qty_on_hand or 0) for row in inventory_rows
        }
        calculation_date = date.today()
        records = []

        for product in products:
            demand_series = _weekly_buckets(demand_by_product.get(product.id, []))
            if not demand_series:
                demand_series = [0.0]
            lead_time_series = lead_times_by_product.get(product.id) or [11.0, 14.0, 17.0]
            segment = segments_by_product.get(product.id)
            target_service_level = service_level_pct
            if (
                target_service_level is None
                and segment
                and segment.target_service_level_pct is not None
            ):
                target_service_level = float(segment.target_service_level_pct)
            if target_service_level is None:
                target_service_level = 95.0

            calc = calculate_safety_stock_ibp(
                demand_series=demand_series,
                lead_time_days_series=lead_time_series,
                service_level_pct=target_service_level,
                period_days=period_days,
            )
            inputs = calc["inputs"]
            components = calc["components"]
            current_stock = inventory_by_product.get(product.id)
            safety_stock_qty = float(calc["safety_stock_qty"])
            delta_qty = None if current_stock is None else current_stock - safety_stock_qty
            delta_pct = None
            if delta_qty is not None and safety_stock_qty:
                delta_pct = delta_qty / safety_stock_qty * 100

            prior = (
                await db.execute(
                    select(SafetyStockRecord)
                    .where(
                        SafetyStockRecord.tenant_id == tenant_id,
                        SafetyStockRecord.product_id == product.id,
                        SafetyStockRecord.calculation_date < calculation_date,
                    )
                    .order_by(SafetyStockRecord.calculation_date.desc())
                    .limit(1)
                )
            ).scalar_one_or_none()
            existing = (
                await db.execute(
                    select(SafetyStockRecord).where(
                        SafetyStockRecord.tenant_id == tenant_id,
                        SafetyStockRecord.product_id == product.id,
                        SafetyStockRecord.calculation_date == calculation_date,
                    )
                )
            ).scalar_one_or_none()
            record = existing or SafetyStockRecord(
                tenant_id=tenant_id,
                product_id=product.id,
                calculation_date=calculation_date,
            )
            if existing is None:
                db.add(record)

            unit_cost = _product_unit_cost(product)
            prior_qty = (
                float(prior.safety_stock_qty)
                if prior and prior.safety_stock_qty is not None
                else None
            )
            cycle_change_qty = safety_stock_qty - prior_qty if prior_qty is not None else None

            record.service_level_target_pct = target_service_level
            record.z_score = calc["z_score"]
            record.avg_demand_per_period = inputs["avg_demand_per_period"]
            record.demand_stddev = inputs["demand_stddev"]
            record.demand_cv = inputs["demand_cv"]
            record.avg_lead_time_periods = inputs["avg_lead_time_periods"]
            record.lead_time_stddev = inputs["lead_time_stddev_periods"]
            record.lead_time_cv = inputs["lead_time_cv"]
            record.safety_stock_qty = safety_stock_qty
            record.safety_stock_demand_component = components["demand_component"]
            record.safety_stock_leadtime_component = components["lead_time_component"]
            record.reorder_point_qty = calc["reorder_point"]
            record.current_stock_qty = current_stock
            record.delta_qty = delta_qty
            record.delta_pct = delta_pct
            record.prior_safety_stock_qty = prior_qty
            record.cycle_change_qty = cycle_change_qty
            record.unit_cost = unit_cost
            record.safety_stock_value = safety_stock_qty * unit_cost
            record.delta_value = delta_qty * unit_cost if delta_qty is not None else None

            records.append(
                {
                    "product_id": str(product.id),
                    "product_name": product.name,
                    "combined_segment": segment.combined_segment if segment else None,
                    "service_level_target_pct": target_service_level,
                    "safety_stock_qty": safety_stock_qty,
                    "reorder_point_qty": float(calc["reorder_point"]),
                    "current_stock_qty": current_stock,
                    "delta_qty": delta_qty,
                    "safety_stock_value": safety_stock_qty * unit_cost,
                    "demand_component": components["demand_component"],
                    "lead_time_component": components["lead_time_component"],
                    "avg_lead_time_days": inputs["avg_lead_time_days"],
                }
            )

        await db.commit()
        return {
            "calculation_date": calculation_date.isoformat(),
            "total_products": len(records),
            "records": records,
        }

    async def latest_results(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        product_id: UUID | None = None,
    ) -> dict:
        latest_date = (
            await db.execute(
                select(func.max(SafetyStockRecord.calculation_date)).where(
                    SafetyStockRecord.tenant_id == tenant_id
                )
            )
        ).scalar_one_or_none()
        if latest_date is None:
            return {"calculation_date": None, "count": 0, "items": []}

        stmt = (
            select(SafetyStockRecord, Product)
            .outerjoin(Product, Product.id == SafetyStockRecord.product_id)
            .where(
                SafetyStockRecord.tenant_id == tenant_id,
                SafetyStockRecord.calculation_date == latest_date,
            )
            .order_by(Product.name)
        )
        if product_id:
            stmt = stmt.where(SafetyStockRecord.product_id == product_id)
        rows = (await db.execute(stmt)).all()
        items = [self._record_to_dict(record, product) for record, product in rows]
        return {"calculation_date": latest_date.isoformat(), "count": len(items), "items": items}

    async def summary(self, db: AsyncSession, tenant_id: UUID) -> dict:
        results = await self.latest_results(db, tenant_id)
        items = results["items"]
        shortage_items = [item for item in items if (item.get("delta_qty") or 0) < 0]
        total_value = sum(float(item.get("safety_stock_value") or 0) for item in items)
        return {
            "calculation_date": results["calculation_date"],
            "total_products": len(items),
            "below_safety_stock_count": len(shortage_items),
            "total_safety_stock_value": round(total_value, 2),
            "items_below_safety_stock": shortage_items,
        }

    async def lead_time_summary(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        product_id: UUID | None = None,
    ) -> dict:
        stmt = select(LeadTimeHistory).where(LeadTimeHistory.tenant_id == tenant_id)
        if product_id:
            stmt = stmt.where(LeadTimeHistory.product_id == product_id)
        rows = (await db.execute(stmt)).scalars().all()
        values_by_product: dict[UUID, list[float]] = defaultdict(list)
        for row in rows:
            if row.lead_time_days is not None:
                values_by_product[row.product_id].append(float(row.lead_time_days))

        items = []
        for pid, values in values_by_product.items():
            avg = sum(values) / len(values)
            stddev = _sample_std(values)
            items.append(
                {
                    "product_id": str(pid),
                    "sample_size": len(values),
                    "avg_lead_time_days": round(avg, 2),
                    "lead_time_stddev_days": round(stddev, 2),
                    "lead_time_cv": round(stddev / avg, 4) if avg else 0.0,
                }
            )
        return {"count": len(items), "items": items}

    @staticmethod
    def _record_to_dict(record: SafetyStockRecord, product: Product | None = None) -> dict:
        return {
            "product_id": str(record.product_id),
            "product_name": product.name if product else None,
            "calculation_date": record.calculation_date.isoformat(),
            "service_level_target_pct": float(record.service_level_target_pct or 0),
            "z_score": float(record.z_score or 0),
            "avg_demand_per_period": float(record.avg_demand_per_period or 0),
            "demand_stddev": float(record.demand_stddev or 0),
            "demand_cv": float(record.demand_cv or 0),
            "avg_lead_time_periods": float(record.avg_lead_time_periods or 0),
            "lead_time_stddev": float(record.lead_time_stddev or 0),
            "lead_time_cv": float(record.lead_time_cv or 0),
            "safety_stock_qty": float(record.safety_stock_qty or 0),
            "safety_stock_demand_component": float(record.safety_stock_demand_component or 0),
            "safety_stock_leadtime_component": float(record.safety_stock_leadtime_component or 0),
            "reorder_point_qty": float(record.reorder_point_qty or 0),
            "current_stock_qty": float(record.current_stock_qty)
            if record.current_stock_qty is not None
            else None,
            "delta_qty": float(record.delta_qty) if record.delta_qty is not None else None,
            "delta_pct": float(record.delta_pct) if record.delta_pct is not None else None,
            "safety_stock_value": float(record.safety_stock_value or 0),
            "delta_value": float(record.delta_value) if record.delta_value is not None else None,
        }
