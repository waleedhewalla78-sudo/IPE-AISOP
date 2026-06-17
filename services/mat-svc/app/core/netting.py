from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.supplier_model import adjust_expected_date
from ipe_shared.models.bom import BillOfMaterial, BomLine
from ipe_shared.models.inventory import InventoryPosition
from ipe_shared.models.supplier import Supplier
from ipe_shared.models.supply import SupplyOrder

DEMAND_TYPE_PRIORITY = {"MTO": 0, "MTS": 1, "ETO": 0, "CTO": 0}


async def get_current_inventory(
    session: AsyncSession, tenant_id: UUID, product_id: UUID
) -> dict:
    result = await session.execute(
        select(InventoryPosition)
        .where(InventoryPosition.tenant_id == tenant_id)
        .where(InventoryPosition.product_id == product_id)
        .order_by(InventoryPosition.time.desc())
        .limit(1)
    )
    row = result.scalar_one_or_none()
    if row is None:
        return {"qty_on_hand": 0, "qty_reserved": 0, "qty_in_transit": 0}
    return {
        "qty_on_hand": float(row.qty_on_hand or 0),
        "qty_reserved": float(row.qty_reserved or 0),
        "qty_in_transit": float(row.qty_in_transit or 0),
    }


async def get_open_supply(
    session: AsyncSession, tenant_id: UUID, product_id: UUID
) -> list[dict]:
    result = await session.execute(
        select(SupplyOrder, Supplier)
        .outerjoin(Supplier, SupplyOrder.supplier_id == Supplier.id)
        .where(SupplyOrder.tenant_id == tenant_id)
        .where(SupplyOrder.product_id == product_id)
        .where(SupplyOrder.status.in_(["confirmed", "in_transit"]))
        .order_by(SupplyOrder.expected_date.asc())
    )
    rows = []
    for supply, supplier in result:
        expected_date = supply.expected_date
        adj = None
        if supplier and supplier.avg_delay_days:
            adj = adjust_expected_date(
                expected_date,
                supplier.avg_delay_days,
                supplier.delay_std_dev_days,
            )
        rows.append({
            "id": str(supply.id),
            "quantity_ordered": float(supply.quantity_ordered or 0),
            "quantity_received": float(supply.quantity_received or 0),
            "expected_date": expected_date.isoformat(),
            "status": supply.status,
            "supplier_name": supplier.name if supplier else None,
            "adjusted_date": adj["adjusted_date"] if adj else expected_date.isoformat(),
            "p90_date": adj["p90_date"] if adj else expected_date.isoformat(),
            "expected_delay_days": adj["expected_delay_days"] if adj else 0.0,
            "confidence": adj["confidence"] if adj else 0.0,
        })
    return rows


async def get_bom_requirements(
    session: AsyncSession, tenant_id: UUID, product_id: UUID
) -> list[dict]:
    result = await session.execute(
        select(BomLine, BillOfMaterial)
        .join(BillOfMaterial, BomLine.bom_id == BillOfMaterial.id)
        .where(BillOfMaterial.tenant_id == tenant_id)
        .where(BillOfMaterial.product_id == product_id)
        .where(BillOfMaterial.is_active.is_(True))
    )
    rows = []
    for bline, _bom in result:
        rows.append({
            "component_id": str(bline.component_id),
            "quantity_per": float(bline.quantity_per or 1),
            "scrap_rate_pct": float(bline.scrap_rate_pct or 0),
            "is_critical": bool(bline.is_critical),
        })
    return rows


async def cumulative_netting(
    session: AsyncSession,
    tenant_id: UUID,
    product_id: UUID,
    demand_quantity: float,
    required_date: datetime | None = None,
) -> dict:
    inventory = await get_current_inventory(session, tenant_id, product_id)
    supply_orders = await get_open_supply(session, tenant_id, product_id)

    available = inventory["qty_on_hand"] - inventory["qty_reserved"]
    incoming_total = sum(
        s["quantity_ordered"] - s["quantity_received"] for s in supply_orders
    )
    net_available = available + incoming_total - demand_quantity

    projected_availability = [
        {
            "date": s["adjusted_date"],
            "quantity": s["quantity_ordered"] - s["quantity_received"],
            "source": "supply_order",
            "confidence": s["confidence"],
        }
        for s in supply_orders
    ]

    return {
        "product_id": str(product_id),
        "qty_on_hand": inventory["qty_on_hand"],
        "qty_reserved": inventory["qty_reserved"],
        "qty_available": available,
        "incoming_supply_total": incoming_total,
        "demand_quantity": demand_quantity,
        "net_available": round(net_available, 4),
        "shortage_quantity": round(max(-net_available, 0), 4),
        "is_available": net_available >= 0,
        "projected_availability": projected_availability,
        "supply_orders": supply_orders,
    }


async def priority_weighted_netting(
    session: AsyncSession,
    tenant_id: UUID,
    product_id: UUID,
    demands: list[dict],
    time_bucket_days: int = 30,
) -> dict:
    inventory = await get_current_inventory(session, tenant_id, product_id)
    supply_orders = await get_open_supply(session, tenant_id, product_id)
    bom_requirements = await get_bom_requirements(session, tenant_id, product_id)

    available = inventory["qty_on_hand"] - inventory["qty_reserved"]

    sorted_demands = sorted(
        demands,
        key=lambda d: (
            DEMAND_TYPE_PRIORITY.get(d.get("demand_type", "MTO"), 0),
            -float(d.get("priority_score", 0) or 0),
            d.get("required_date", ""),
        ),
    )

    allocations = []
    remaining_supply = sum(
        s["quantity_ordered"] - s["quantity_received"] for s in supply_orders
    )
    cumulative_allocated = 0.0

    for demand in sorted_demands:
        qty = float(demand.get("quantity", 0))
        demand_type = demand.get("demand_type", "MTO")
        priority_score = float(demand.get("priority_score", 0) or 0)
        allocated = min(qty, available + remaining_supply - cumulative_allocated)
        cumulative_allocated += allocated
        allocations.append({
            "demand_id": str(demand.get("id", "")),
            "demand_type": demand_type,
            "priority_score": priority_score,
            "requested": qty,
            "allocated": round(allocated, 4),
            "shortfall": round(max(qty - allocated, 0), 4),
            "is_fully_allocated": allocated >= qty,
        })

    net_available = available + remaining_supply - sum(
        a["requested"] for a in allocations
    )

    contentions = await detect_contentions(
        session, tenant_id, product_id, demands, supply_orders, time_bucket_days
    )

    return {
        "product_id": str(product_id),
        "qty_on_hand": inventory["qty_on_hand"],
        "qty_available": available,
        "total_supply_incoming": remaining_supply,
        "total_demand_requested": sum(a["requested"] for a in allocations),
        "net_position": round(net_available, 4),
        "allocations": allocations,
        "contentions": contentions,
        "bom_requirements": bom_requirements,
    }


async def detect_contentions(
    session: AsyncSession,
    tenant_id: UUID,
    product_id: UUID,
    demands: list[dict],
    supply_orders: list[dict],
    time_bucket_days: int = 30,
) -> list[dict]:
    contentions = []

    total_supply = sum(
        s["quantity_ordered"] - s["quantity_received"] for s in supply_orders
    )
    total_demand = sum(float(d.get("quantity", 0)) for d in demands)

    if total_demand > total_supply:
        shortage = total_demand - total_supply
        contentions.append({
            "product_id": str(product_id),
            "type": "cumulative_shortage",
            "severity": "critical" if shortage > total_supply * 0.5 else "warning",
            "total_demand": round(total_demand, 4),
            "total_supply": round(total_supply, 4),
            "shortage": round(shortage, 4),
            "time_bucket_days": time_bucket_days,
            "detail": f"Total demand ({total_demand:.1f}) exceeds total supply ({total_supply:.1f}) by {shortage:.1f}",
        })

    urgent_overlap_count = 0
    for demand in demands:
        if (
            float(demand.get("priority_score", 0) or 0) >= 0.8
            and float(demand.get("quantity", 0)) > total_supply * 0.3
        ):
            urgent_overlap_count += 1

    if urgent_overlap_count > 1:
        contentions.append({
            "product_id": str(product_id),
            "type": "urgent_demand_overlap",
            "severity": "high",
            "overlapping_urgent_count": urgent_overlap_count,
            "detail": f"{urgent_overlap_count} high-priority demands compete for limited supply",
        })

    return contentions
