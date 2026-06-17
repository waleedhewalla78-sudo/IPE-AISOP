import math
import random
from collections import defaultdict
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.netting import get_current_inventory, get_open_supply


async def simulate_atp(
    session: AsyncSession,
    tenant_id: UUID,
    product_id: UUID,
    quantity: float,
    required_date: datetime,
    num_simulations: int = 5000,
) -> dict:
    inventory = await get_current_inventory(session, tenant_id, product_id)
    supply_rows = await get_open_supply(session, tenant_id, product_id)

    available_now = inventory["qty_on_hand"] - inventory["qty_reserved"]

    supply_samples: dict[str, list[float]] = defaultdict(list)
    for s in supply_rows:
        mean = s["expected_delay_days"]
        std = max(s.get("delay_std_dev", mean * 0.3), 0.001)
        for _ in range(num_simulations):
            delay = random.gauss(mean, std)
            supply_samples[s["id"]].append(max(0.0, delay))

    successful = 0
    atp_quantiles: list[float] = []

    for sim_idx in range(num_simulations):
        sim_available = available_now
        for s in supply_rows:
            delay = supply_samples[s["id"]][sim_idx]
            arrival = s["expected_date"]
            from datetime import timedelta
            adjusted = arrival + timedelta(days=delay)
            if adjusted <= required_date:
                sim_available += s["quantity_ordered"] - s["quantity_received"]
        if sim_available >= quantity:
            successful += 1
        atp_quantiles.append(sim_available)

    atp_quantiles.sort()
    p10 = atp_quantiles[int(num_simulations * 0.1)]
    p50 = atp_quantiles[int(num_simulations * 0.5)]
    p90 = atp_quantiles[int(num_simulations * 0.9)]
    confidence = successful / num_simulations if num_simulations > 0 else 0.0

    estimated_date = None
    if p50 < quantity:
        cumulative = available_now
        sorted_supply = sorted(supply_rows, key=lambda s: s["adjusted_date"])
        for s in sorted_supply:
            cumulative += s["quantity_ordered"] - s["quantity_received"]
            if cumulative >= quantity:
                estimated_date = s["adjusted_date"]
                break
        if estimated_date is None and sorted_supply:
            estimated_date = sorted_supply[-1]["adjusted_date"]

    return {
        "product_id": str(product_id),
        "quantity_requested": quantity,
        "required_date": required_date.isoformat(),
        "atp_quantity": round(p50, 4),
        "confidence": round(confidence, 4),
        "is_available": confidence >= 0.9,
        "estimated_available_date": estimated_date,
        "p10": round(p10, 4),
        "p50": round(p50, 4),
        "p90": round(p90, 4),
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
    inventory = await get_current_inventory(session, tenant_id, product_id)
    supply_rows = await get_open_supply(session, tenant_id, product_id)

    available_now = inventory["qty_on_hand"] - inventory["qty_reserved"]

    cumulative_available = available_now
    estimated_available_date = None
    supply_contributions = []

    for s in sorted(supply_rows, key=lambda x: x["adjusted_date"]):
        delivery_date = datetime.fromisoformat(s["adjusted_date"].replace("Z", "+00:00"))
        effective_date = delivery_date + timedelta(days=delay_buffer_days)
        qty = s["quantity_ordered"] - s["quantity_received"]
        prev_cumulative = cumulative_available
        cumulative_available += qty

        supply_contributions.append({
            "supply_id": s["id"],
            "supplier_name": s["supplier_name"],
            "original_date": s["adjusted_date"],
            "effective_date": effective_date.isoformat(),
            "quantity": qty,
            "cumulative_before": round(prev_cumulative, 4),
            "cumulative_after": round(cumulative_available, 4),
        })

        if estimated_available_date is None and cumulative_available >= quantity and effective_date <= required_date:
            estimated_available_date = effective_date.isoformat()

        if estimated_available_date is None and cumulative_available >= quantity:
            estimated_available_date = effective_date.isoformat()

    final_available = cumulative_available
    is_available_now = available_now >= quantity
    is_available_by_required = final_available >= quantity and (
        estimated_available_date is None
        or datetime.fromisoformat(estimated_available_date.replace("Z", "+00:00")) <= required_date
    )

    final_available_by_required = available_now
    for s in sorted(supply_rows, key=lambda x: x["adjusted_date"]):
        delivery_date = datetime.fromisoformat(s["adjusted_date"].replace("Z", "+00:00"))
        effective_date = delivery_date + timedelta(days=delay_buffer_days)
        if effective_date <= required_date:
            final_available_by_required += s["quantity_ordered"] - s["quantity_received"]

    atp_quantity = min(final_available_by_required, quantity) if is_available_by_required else 0

    return {
        "product_id": str(product_id),
        "quantity_requested": quantity,
        "required_date": required_date.isoformat(),
        "atp_quantity": round(atp_quantity, 4),
        "is_available_now": is_available_now,
        "is_available_by_required": is_available_by_required,
        "estimated_available_date": estimated_available_date,
        "available_now": round(available_now, 4),
        "available_by_required": round(final_available_by_required, 4),
        "total_available_at_required": round(final_available_by_required, 4),
        "delay_buffer_days": delay_buffer_days,
        "rule_based": True,
        "supply_contributions": supply_contributions,
    }


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
