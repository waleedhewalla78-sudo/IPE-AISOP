import math
import random
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.netting import get_current_inventory, get_open_supply
from ipe_shared.models.bom import BomLine
from ipe_shared.models.manufacturing_order import ManufacturingOrder
from ipe_shared.models.supplier import Supplier


def _sample_delay(distribution_type: str, mean: float, std: float) -> float:
    if distribution_type == "lognormal":
        if mean <= 0:
            return 0.0
        mu = math.log(mean**2 / math.sqrt(std**2 + mean**2))
        sigma = math.sqrt(math.log(1 + (std**2 / mean**2)))
        return max(0.0, random.lognormvariate(mu, sigma))
    return max(0.0, random.gauss(mean, std))


def _component_monte_carlo(
    on_hand: float,
    reserved: float,
    supply_orders: list[dict],
    required_qty: float,
    required_date: datetime,
    priority_demand: float,
    num_simulations: int,
) -> dict:
    available_now = on_hand - reserved - priority_demand
    sim_results: list[bool] = []
    for _ in range(num_simulations):
        sim_available = available_now
        for s in supply_orders:
            delay = _sample_delay(
                s.get("distribution_type", "normal"),
                s.get("expected_delay_days", 0.0),
                max(s.get("delay_std_dev", s.get("expected_delay_days", 0.0) * 0.3), 0.001),
            )
            arrival = datetime.fromisoformat(s["expected_date"].replace("Z", "+00:00"))
            adjusted = arrival + timedelta(days=delay)
            if adjusted <= required_date:
                sim_available += s["quantity_ordered"] - s["quantity_received"]
        sim_results.append(sim_available >= required_qty)
    confidence = sum(sim_results) / num_simulations
    return {
        "confidence": round(confidence, 4),
        "available_now": round(max(available_now, 0), 4),
        "is_available_now": available_now >= required_qty,
    }


async def get_mo_by_id(
    session: AsyncSession,
    tenant_id: UUID,
    mo_id: UUID,
) -> ManufacturingOrder | None:
    result = await session.execute(
        select(ManufacturingOrder)
        .where(ManufacturingOrder.id == mo_id)
        .where(ManufacturingOrder.tenant_id == tenant_id)
    )
    return result.scalar_one_or_none()


async def get_bom_components(
    session: AsyncSession,
    tenant_id: UUID,
    bom_id: UUID,
) -> list[dict]:
    result = await session.execute(
        select(BomLine)
        .where(BomLine.bom_id == bom_id)
    )
    components = []
    for row in result.scalars().all():
        components.append({
            "component_id": str(row.component_id),
            "quantity_per": float(row.quantity_per),
            "scrap_rate_pct": float(row.scrap_rate_pct or 0),
            "is_critical": bool(row.is_critical),
        })
    return components


async def compute_material_score(
    mo_id: UUID,
    tenant_id: UUID,
    session: AsyncSession,
    num_simulations: int = 5000,
) -> dict:
    mo = await get_mo_by_id(session, tenant_id, mo_id)
    if mo is None:
        return {"mo_id": str(mo_id), "error": "Manufacturing order not found"}

    bom_id = mo.bom_id
    mo_qty = float(mo.quantity)
    required_date = mo.planned_start or datetime.now()

    components = await get_bom_components(session, tenant_id, bom_id)

    component_breakdown = []
    overall_probability = 1.0
    bottleneck_component = None
    bottleneck_probability = 1.0
    method = "fallback"

    supplier_max_sample = await session.execute(
        select(Supplier.sample_size)
        .where(Supplier.tenant_id == tenant_id)
        .order_by(Supplier.sample_size.desc())
        .limit(1)
    )
    top_sample = supplier_max_sample.scalar_one_or_none()
    if top_sample is not None and top_sample >= 30:
        method = "monte_carlo"

    for comp in components:
        comp_id = UUID(comp["component_id"])
        qty_per = comp["quantity_per"]
        scrap_pct = comp["scrap_rate_pct"]
        required_qty = qty_per * mo_qty * (1 + scrap_pct / 100.0)

        inv = await get_current_inventory(session, tenant_id, comp_id)
        supply_rows = await get_open_supply(session, tenant_id, comp_id)

        mc = _component_monte_carlo(
            on_hand=inv["qty_on_hand"],
            reserved=inv["qty_reserved"],
            supply_orders=supply_rows,
            required_qty=required_qty,
            required_date=required_date,
            priority_demand=0,
            num_simulations=num_simulations,
        )

        on_time_probability = mc["confidence"]
        overall_probability *= on_time_probability

        if on_time_probability < bottleneck_probability:
            bottleneck_probability = on_time_probability
            bottleneck_component = comp["component_id"]

        component_breakdown.append({
            "component_id": comp["component_id"],
            "required_qty": round(required_qty, 4),
            "available_now": mc["available_now"],
            "is_available_now": mc["is_available_now"],
            "on_time_probability": on_time_probability,
        })

    material_score = round(overall_probability * 100, 2)

    await session.execute(
        update(ManufacturingOrder)
        .where(ManufacturingOrder.id == mo_id)
        .where(ManufacturingOrder.tenant_id == tenant_id)
        .values(material_score=material_score)
    )
    await session.commit()

    return {
        "mo_id": str(mo_id),
        "material_score": material_score,
        "overall_probability": round(overall_probability, 4),
        "bottleneck_component": bottleneck_component or "",
        "method": method,
        "component_breakdown": component_breakdown,
    }


async def simulate_atp(
    session: AsyncSession,
    tenant_id: UUID,
    product_id: UUID,
    quantity: float,
    required_date: datetime,
    num_simulations: int = 1000,
) -> dict:
    """Simplified ATP check for a single product.

    Runs Monte Carlo simulation against current inventory and open supply
    to determine availability confidence at the required date.
    """
    inv = await get_current_inventory(session, tenant_id, product_id)
    supply_rows = await get_open_supply(session, tenant_id, product_id)

    mc = _component_monte_carlo(
        on_hand=inv["qty_on_hand"],
        reserved=inv["qty_reserved"],
        supply_orders=supply_rows,
        required_qty=quantity,
        required_date=required_date,
        priority_demand=0,
        num_simulations=num_simulations,
    )

    available_now = inv["qty_on_hand"] - inv["qty_reserved"]
    in_transit = inv.get("qty_in_transit", 0)

    supply_arriving = sum(
        s["quantity_ordered"] - s["quantity_received"]
        for s in supply_rows
        if s.get("adjusted_date")
        and datetime.fromisoformat(s["adjusted_date"].replace("Z", "+00:00")) <= required_date
    )

    return {
        "product_id": str(product_id),
        "quantity_requested": quantity,
        "required_date": required_date.isoformat(),
        "is_available": mc["is_available_now"],
        "availability_p90": round(mc["confidence"], 4),
        "available_now": round(max(available_now, 0), 4),
        "in_transit": round(in_transit, 4),
        "supply_arriving_by_date": round(supply_arriving, 4),
        "num_simulations": num_simulations,
    }


async def rule_based_atp(
    session: AsyncSession,
    tenant_id: UUID,
    product_id: UUID,
    quantity: float,
    required_date: datetime,
    delay_buffer_days: float = 1.5,
) -> dict:
    """Deterministic rule-based ATP with configurable delay buffer.

    Unlike probabilistic_atp, this does NOT run Monte Carlo. It applies a
    fixed delay buffer to each supply order's expected arrival date and
    checks deterministic availability.
    """
    inv = await get_current_inventory(session, tenant_id, product_id)
    supply_rows = await get_open_supply(session, tenant_id, product_id)

    available_now = inv["qty_on_hand"] - inv["qty_reserved"]
    cumulative = available_now

    buffer = timedelta(days=delay_buffer_days)
    supply_breakdown = []
    for s in supply_rows:
        expected = datetime.fromisoformat(s["expected_date"].replace("Z", "+00:00"))
        buffered_arrival = expected + buffer
        qty_remaining = s["quantity_ordered"] - s["quantity_received"]
        arrives_on_time = buffered_arrival <= required_date
        cumulative += qty_remaining if arrives_on_time else 0
        supply_breakdown.append({
            "supply_order_id": s.get("supply_order_id", ""),
            "supplier_id": s.get("supplier_id", ""),
            "quantity_ordered": s["quantity_ordered"],
            "quantity_received": s["quantity_received"],
            "expected_date": s["expected_date"],
            "buffered_arrival_date": buffered_arrival.isoformat(),
            "arrives_on_time": arrives_on_time,
            "contribution": qty_remaining if arrives_on_time else 0,
        })

    is_available = cumulative >= quantity
    shortage = max(0, quantity - cumulative)

    return {
        "product_id": str(product_id),
        "quantity_requested": quantity,
        "required_date": required_date.isoformat(),
        "delay_buffer_days": delay_buffer_days,
        "is_available": is_available,
        "available_now": round(max(available_now, 0), 4),
        "total_after_buffered_supply": round(cumulative, 4),
        "shortage": round(shortage, 4),
        "supply_contribution_breakdown": supply_breakdown,
    }


async def probabilistic_atp(
    session: AsyncSession,
    tenant_id: UUID,
    mo: dict,
    components: list[dict],
    priority_queue: list[dict],
    required_start: datetime,
    num_simulations: int = 5000,
) -> dict:
    component_results = []
    bottleneck_id = None
    bottleneck_confidence = 1.0
    earliest_feasible = None

    for comp in components:
        comp_id = comp.get("component_id", str(comp.get("id", "")))
        comp_qty = comp.get("quantity_per", 1) * mo.get("quantity", 1)

        inv = await get_current_inventory(session, tenant_id, UUID(comp_id))
        supply_rows = await get_open_supply(session, tenant_id, UUID(comp_id))

        priority_demand = sum(
            float(d.get("quantity", 0))
            for d in priority_queue
            if d.get("product_id", "").strip().lower() == comp_id.strip().lower()
        )

        mc = _component_monte_carlo(
            on_hand=inv["qty_on_hand"],
            reserved=inv["qty_reserved"],
            supply_orders=supply_rows,
            required_qty=comp_qty,
            required_date=required_start,
            priority_demand=priority_demand,
            num_simulations=num_simulations,
        )

        earliest_available_date = None
        if not mc["is_available_now"]:
            cumulative = mc["available_now"]
            sorted_supply = sorted(supply_rows, key=lambda s: s["adjusted_date"])
            for s in sorted_supply:
                cumulative += s["quantity_ordered"] - s["quantity_received"]
                if cumulative >= comp_qty:
                    earliest_available_date = s["adjusted_date"]
                    break
            if earliest_available_date is None and sorted_supply:
                earliest_available_date = sorted_supply[-1]["adjusted_date"]

        cr = {
            "component_id": comp_id,
            "required_quantity": comp_qty,
            "available_now": mc["available_now"],
            "confidence": mc["confidence"],
            "is_available_now": mc["is_available_now"],
            "earliest_available_date": earliest_available_date,
        }
        component_results.append(cr)

        if mc["confidence"] < bottleneck_confidence:
            bottleneck_confidence = mc["confidence"]
            bottleneck_id = comp_id

        comp_earliest = (
            datetime.fromisoformat(earliest_available_date.replace("Z", "+00:00"))
            if earliest_available_date
            else None
        )
        if comp_earliest and (
            earliest_feasible is None or comp_earliest > earliest_feasible
        ):
            earliest_feasible = comp_earliest

    return {
        "mo_id": str(mo.get("id", "")),
        "mo_number": mo.get("mo_number", ""),
        "required_start": required_start.isoformat(),
        "overall_confidence": round(bottleneck_confidence, 4),
        "bottleneck_component_id": bottleneck_id or "",
        "earliest_feasible_start_date": (
            earliest_feasible.isoformat() if earliest_feasible else None
        ),
        "component_breakdown": component_results,
        "num_simulations": num_simulations,
    }
