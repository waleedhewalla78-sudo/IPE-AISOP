"""Resolve manufacturing order priority for CP-SAT tardiness weighting."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ipe_shared.models.activity_cost import ActivityCostDriver
from ipe_shared.models.demand import DemandLine
from ipe_shared.models.manufacturing_order import ManufacturingOrder
from ipe_shared.models.product import Product
from ipe_shared.models.routing import RoutingOperation

FEASIBILITY_GUARDRAIL_THRESHOLD = 85.0


def normalize_priority(raw: float) -> float:
    """Map stored priority (0-1 or 0-100) to solver weight in (0.01, 1.0]."""
    value = float(raw)
    if value > 1.0:
        value = value / 100.0
    return min(1.0, max(0.01, value))


async def resolve_mo_priority(
    session: AsyncSession,
    tenant_id: UUID,
    mo: ManufacturingOrder,
) -> float:
    """Prefer dpe-svc demand priority; fall back to feasibility score."""
    result = await session.execute(
        select(func.max(DemandLine.priority_score)).where(
            DemandLine.tenant_id == tenant_id,
            DemandLine.mo_id == mo.id,
            DemandLine.priority_score.isnot(None),
        )
    )
    demand_priority = result.scalar()
    if demand_priority is not None:
        return normalize_priority(float(demand_priority))

    if mo.feasibility_score is not None:
        return normalize_priority(float(mo.feasibility_score))

    return 0.5


async def resolve_mo_priority_margin_aware(
    session: AsyncSession,
    tenant_id: UUID,
    mo: ManufacturingOrder,
) -> tuple[float, str | None]:
    """Margin-adjusted weight for activity-based scheduling; warning if drivers missing."""
    base = await resolve_mo_priority(session, tenant_id, mo)
    base_score = base * 100.0 if base <= 1.0 else base

    driver_result = await session.execute(
        select(ActivityCostDriver).where(
            ActivityCostDriver.tenant_id == tenant_id,
            ActivityCostDriver.product_id == mo.product_id,
        )
    )
    driver = driver_result.scalar_one_or_none()
    if not driver:
        return base, "MISSING_COST_DRIVER"

    product_result = await session.execute(
        select(Product).where(Product.id == mo.product_id, Product.tenant_id == tenant_id)
    )
    product = product_result.scalar_one_or_none()
    if not product or product.standard_cost is None:
        return base, "MISSING_COST_DRIVER"

    qty = float(mo.quantity or 1)
    unit_price = float(product.standard_cost) * 1.35
    revenue = unit_price * qty
    cogs = float(product.standard_cost) * qty

    routing_result = await session.execute(
        select(RoutingOperation).where(
            RoutingOperation.tenant_id == tenant_id,
            RoutingOperation.bom_id == mo.bom_id,
        )
    )
    routing_ops = routing_result.scalars().all()
    op_count = max(1, len(routing_ops))
    setup_cost = (float(driver.setup_mins or 0) * op_count / 60.0) * float(driver.overtime_rate_usd_per_hr or 0)
    overhead = revenue * float(driver.overhead_pct or 0)
    expedite = float(driver.expedite_cost_per_unit or 0) * qty
    net_margin = revenue - cogs - setup_cost - overhead - expedite

    max_ref = max(revenue * 0.5, 1.0)
    margin_component = min(100.0, max(0.0, (net_margin / max_ref) * 100.0))
    adjusted = min(100.0, max(1.0, 0.4 * base_score + 0.6 * margin_component))
    return normalize_priority(adjusted), None


def passes_feasibility_guardrail(feasibility_score: float | None) -> bool:
    if feasibility_score is None:
        return True
    return float(feasibility_score) >= FEASIBILITY_GUARDRAIL_THRESHOLD
