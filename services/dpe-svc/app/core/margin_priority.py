"""Net-margin-aware priority using activity cost drivers and product economics."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ipe_shared.models.activity_cost import ActivityCostDriver
from ipe_shared.models.demand import DemandLine
from ipe_shared.models.manufacturing_order import ManufacturingOrder
from ipe_shared.models.product import Product
from ipe_shared.models.routing import RoutingOperation


@dataclass
class MarginPriorityResult:
    mo_id: str
    base_priority_score: float
    margin_adjusted_score: float
    net_margin_usd: float
    activity_overhead_usd: float
    data_quality: str
    warning: str | None = None


def _normalize_margin_to_score(net_margin: float, max_margin: float) -> float:
    if max_margin <= 0:
        return 50.0
    ratio = min(1.0, max(0.0, net_margin / max_margin))
    return round(ratio * 100.0, 2)


async def _load_activity_driver(
    session: AsyncSession,
    tenant_id: UUID,
    product_id: UUID,
) -> ActivityCostDriver | None:
    result = await session.execute(
        select(ActivityCostDriver).where(
            ActivityCostDriver.tenant_id == tenant_id,
            ActivityCostDriver.product_id == product_id,
        )
    )
    return result.scalar_one_or_none()


async def compute_margin_adjusted_priority(
    session: AsyncSession,
    tenant_id: UUID,
    mo: ManufacturingOrder,
) -> MarginPriorityResult:
    """Compute margin-adjusted priority for a single MO."""
    base_result = await session.execute(
        select(DemandLine.priority_score).where(
            DemandLine.tenant_id == tenant_id,
            DemandLine.mo_id == mo.id,
            DemandLine.priority_score.isnot(None),
        )
    )
    base_priority = base_result.scalar()
    if base_priority is not None:
        base_score = float(base_priority)
    elif mo.feasibility_score is not None:
        base_score = float(mo.feasibility_score)
    else:
        base_score = 50.0

    product_result = await session.execute(
        select(Product).where(Product.id == mo.product_id, Product.tenant_id == tenant_id)
    )
    product = product_result.scalar_one_or_none()
    if not product:
        return MarginPriorityResult(
            mo_id=str(mo.id),
            base_priority_score=base_score,
            margin_adjusted_score=base_score,
            net_margin_usd=0.0,
            activity_overhead_usd=0.0,
            data_quality="missing_product",
            warning="MISSING_PRODUCT",
        )

    driver = await _load_activity_driver(session, tenant_id, mo.product_id)
    if not driver:
        return MarginPriorityResult(
            mo_id=str(mo.id),
            base_priority_score=base_score,
            margin_adjusted_score=base_score,
            net_margin_usd=0.0,
            activity_overhead_usd=0.0,
            data_quality="missing_cost_driver",
            warning="MISSING_COST_DRIVER",
        )

    qty = float(mo.quantity or 1)
    unit_price = float(product.standard_cost or 0) * 1.35
    revenue = unit_price * qty
    cogs = float(product.standard_cost or 0) * qty

    routing_result = await session.execute(
        select(RoutingOperation).where(
            RoutingOperation.tenant_id == tenant_id,
            RoutingOperation.bom_id == mo.bom_id,
        )
    )
    routing_ops = routing_result.scalars().all()
    op_count = max(1, len(routing_ops))
    setup_mins = float(driver.setup_mins or 15)
    setup_cost = (setup_mins / 60.0) * float(driver.overtime_rate_usd_per_hr or 0)
    overhead = revenue * float(driver.overhead_pct or 0)
    expedite = float(driver.expedite_cost_per_unit or 0) * qty
    activity_overhead = setup_cost + overhead + expedite
    net_margin = revenue - cogs - activity_overhead

    margin_component = _normalize_margin_to_score(net_margin, revenue * 0.5)
    margin_adjusted = round(min(100.0, max(1.0, 0.4 * base_score + 0.6 * margin_component)), 2)

    return MarginPriorityResult(
        mo_id=str(mo.id),
        base_priority_score=round(base_score, 2),
        margin_adjusted_score=margin_adjusted,
        net_margin_usd=round(net_margin, 2),
        activity_overhead_usd=round(activity_overhead, 2),
        data_quality="complete",
    )


async def compute_margin_priorities_for_mos(
    session: AsyncSession,
    tenant_id: UUID,
    mo_ids: list[UUID] | None = None,
) -> tuple[list[MarginPriorityResult], list[dict]]:
    query = select(ManufacturingOrder).where(ManufacturingOrder.tenant_id == tenant_id)
    if mo_ids:
        query = query.where(ManufacturingOrder.id.in_(mo_ids))
    result = await session.execute(query)
    mos = result.scalars().all()

    priorities: list[MarginPriorityResult] = []
    warnings: list[dict] = []
    for mo in mos:
        item = await compute_margin_adjusted_priority(session, tenant_id, mo)
        priorities.append(item)
        if item.warning:
            warnings.append({
                "mo_id": item.mo_id,
                "code": item.warning,
                "message": "Fell back to base priority",
            })
    return priorities, warnings
