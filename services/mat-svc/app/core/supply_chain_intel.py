"""Supply chain intelligence helpers (Sprint S10)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ipe_shared.models.inventory import InventoryPosition
from ipe_shared.models.product import Product
from ipe_shared.models.supplier import Supplier
from ipe_shared.models.supply import SupplyOrder


def _risk_tier(score: float, avg_delay: float) -> str:
    if score < 0.6 or avg_delay > 5:
        return "high"
    if score < 0.8 or avg_delay > 2:
        return "medium"
    return "low"


async def compute_supplier_risk(session: AsyncSession, tenant_id: UUID) -> list[dict]:
    suppliers = (
        await session.execute(select(Supplier).where(Supplier.tenant_id == tenant_id))
    ).scalars().all()

    results = []
    for s in suppliers:
        score = float(s.reliability_score or 0.75)
        avg_delay = float(s.avg_delay_days or 0)
        tier = s.risk_tier or _risk_tier(score, avg_delay)
        results.append(
            {
                "supplier_id": str(s.id),
                "name": s.name,
                "reliability_score": round(score, 4),
                "avg_delay_days": round(avg_delay, 2),
                "risk_tier": tier,
                "sample_size": int(s.sample_size or 0),
                "category": s.category,
                "contributing_factors": {
                    "reliability": round(score, 4),
                    "delay_exposure": round(min(1.0, avg_delay / 10), 4),
                    "esg_score": float(s.esg_score or 70) / 100,
                },
            }
        )

    results.sort(key=lambda r: r["reliability_score"])
    return results


async def compute_inventory_abc(session: AsyncSession, tenant_id: UUID) -> dict:
    stmt = (
        select(
            Product.id,
            Product.name,
            Product.internal_ref,
            func.coalesce(func.sum(InventoryPosition.qty_on_hand), 0).label("qty_on_hand"),
        )
        .outerjoin(InventoryPosition, InventoryPosition.product_id == Product.id)
        .where(Product.tenant_id == tenant_id)
        .group_by(Product.id, Product.name, Product.internal_ref)
        .order_by(func.coalesce(func.sum(InventoryPosition.qty_on_hand), 0).desc())
    )
    rows = (await session.execute(stmt)).all()
    if not rows:
        return {"items": [], "class_a_count": 0, "class_b_count": 0, "class_c_count": 0}

    total_qty = sum(float(r.qty_on_hand or 0) for r in rows) or 1.0
    cumulative = 0.0
    items = []
    class_counts = {"A": 0, "B": 0, "C": 0}

    for row in rows:
        qty = float(row.qty_on_hand or 0)
        share = qty / total_qty
        cumulative += share
        if cumulative <= 0.8:
            abc_class = "A"
        elif cumulative <= 0.95:
            abc_class = "B"
        else:
            abc_class = "C"
        class_counts[abc_class] += 1
        items.append(
            {
                "product_id": str(row.id),
                "name": row.name,
                "internal_ref": row.internal_ref,
                "qty_on_hand": round(qty, 2),
                "value_share_pct": round(share * 100, 2),
                "cumulative_share_pct": round(cumulative * 100, 2),
                "abc_class": abc_class,
            }
        )

    return {
        "items": items,
        "class_a_count": class_counts["A"],
        "class_b_count": class_counts["B"],
        "class_c_count": class_counts["C"],
    }


async def compute_slow_moving(
    session: AsyncSession,
    tenant_id: UUID,
    stale_days: int = 90,
) -> list[dict]:
    cutoff = datetime.now(UTC) - timedelta(days=stale_days)
    supply_stmt = (
        select(
            Product.id,
            Product.name,
            func.max(SupplyOrder.actual_date).label("last_receipt"),
            func.coalesce(func.sum(InventoryPosition.qty_on_hand), 0).label("qty_on_hand"),
        )
        .outerjoin(SupplyOrder, SupplyOrder.product_id == Product.id)
        .outerjoin(InventoryPosition, InventoryPosition.product_id == Product.id)
        .where(Product.tenant_id == tenant_id)
        .group_by(Product.id, Product.name)
        .having(func.coalesce(func.sum(InventoryPosition.qty_on_hand), 0) > 0)
    )
    rows = (await session.execute(supply_stmt)).all()

    slow = []
    for row in rows:
        last_receipt = row.last_receipt
        days_since = (datetime.now(UTC) - last_receipt).days if last_receipt else stale_days + 1
        if days_since >= stale_days:
            slow.append(
                {
                    "product_id": str(row.id),
                    "name": row.name,
                    "qty_on_hand": round(float(row.qty_on_hand or 0), 2),
                    "days_since_movement": days_since,
                    "last_receipt_at": last_receipt.isoformat() if last_receipt else None,
                }
            )

    slow.sort(key=lambda x: x["days_since_movement"], reverse=True)
    return slow


async def compute_reorder_suggestions(session: AsyncSession, tenant_id: UUID) -> list[dict]:
    stmt = (
        select(
            Product.id,
            Product.name,
            Product.internal_ref,
            func.coalesce(func.sum(InventoryPosition.qty_on_hand), 0).label("qty_on_hand"),
            func.coalesce(func.sum(InventoryPosition.qty_reserved), 0).label("qty_reserved"),
        )
        .outerjoin(InventoryPosition, InventoryPosition.product_id == Product.id)
        .where(Product.tenant_id == tenant_id, Product.source_type == "purchased")
        .group_by(Product.id, Product.name, Product.internal_ref)
    )
    rows = (await session.execute(stmt)).all()

    suggestions = []
    for row in rows:
        on_hand = float(row.qty_on_hand or 0)
        reserved = float(row.qty_reserved or 0)
        available = max(0, on_hand - reserved)
        reorder_point = 50.0
        if available < reorder_point:
            order_qty = max(reorder_point * 2 - available, reorder_point)
            suggestions.append(
                {
                    "product_id": str(row.id),
                    "name": row.name,
                    "internal_ref": row.internal_ref,
                    "qty_available": round(available, 2),
                    "reorder_point": reorder_point,
                    "suggested_order_qty": round(order_qty, 2),
                    "urgency": "high" if available < reorder_point * 0.5 else "medium",
                }
            )

    suggestions.sort(key=lambda s: s["qty_available"])
    return suggestions
