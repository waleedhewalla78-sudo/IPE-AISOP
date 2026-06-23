"""Resolve manufacturing order priority for CP-SAT tardiness weighting."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ipe_shared.models.demand import DemandLine
from ipe_shared.models.manufacturing_order import ManufacturingOrder


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
