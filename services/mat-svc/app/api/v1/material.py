import logging
import math
from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.core.atp import probabilistic_atp, rule_based_atp, simulate_atp
from app.core.landed_cost import compute_landed_cost
from app.core.netting import cumulative_netting, priority_weighted_netting
from app.core.po_suggestion import generate_po_suggestions, merge_po_suggestions
from app.core.safety_stock import calculate_all_products_safety_stock, calculate_safety_stock
from app.core.supplier_model import predict_delay
from app.core.ctp_solver import (
    CTPOrderLine, MaterialAvailability, CapacitySlot,
    solve_ctp,
)
from ipe_shared.auth.rbac import require_roles
from ipe_shared.events.producer import kafka_producer
from ipe_shared.events.schemas import EventEnvelope
from ipe_shared.middleware.tenant_context import tenant_ctx
from ipe_shared.schemas.common import APIResponse
from ipe_shared.schemas.xai import XAIExplanation

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/material", tags=["material"])


class AvailabilityRequest(BaseModel):
    product_id: UUID
    quantity: float
    required_date: str


class NettingRequest(BaseModel):
    product_id: UUID
    quantity: float
    required_date: str | None = None


class PriorityNettingRequest(BaseModel):
    product_id: UUID
    demands: list[dict]
    time_bucket_days: int = 30


class RuleBasedAtpRequest(BaseModel):
    product_id: UUID
    quantity: float
    required_date: str
    delay_buffer_days: float = 1.5


class ProbabilisticAtpRequest(BaseModel):
    mo: dict
    components: list[dict]
    priority_queue: list[dict] = []
    required_start: str
    num_simulations: int = 5000


class SupplierPredictRequest(BaseModel):
    supplier_id: UUID | None = None


class SafetyStockRequest(BaseModel):
    product_id: UUID | None = None
    avg_daily_demand: float | None = None
    demand_std_dev: float | None = None
    avg_lead_time_days: float | None = None
    lead_time_std_dev: float | None = None
    service_level: float = 0.95


class BulkSafetyStockRequest(BaseModel):
    products: list[dict]
    service_level: float = 0.95


class POSuggestionRequest(BaseModel):
    shortages: list[dict]
    suppliers: dict = {}
    service_level: float = 0.95
    holding_cost_pct: float = 0.25
    order_cost: float = 50.0
    merge: bool = True


@router.get("/inventory-summary")
async def inventory_summary(
    include_purchased: bool = False,
    current_user=Depends(require_roles(["admin", "planner", "manager", "supervisor", "auditor"])),
    session: AsyncSession = Depends(get_db_session),
):
    """Return on-hand inventory grouped by product (FG stock by default)."""
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})

    from sqlalchemy import func, select as sa_select
    from ipe_shared.models.inventory import InventoryPosition
    from ipe_shared.models.product import Product

    tid = UUID(tenant_id)
    stmt = (
        sa_select(
            Product.id,
            Product.name,
            Product.internal_ref,
            Product.erp_source_id,
            Product.uom,
            Product.source_type,
            func.coalesce(func.sum(InventoryPosition.qty_on_hand), 0).label("qty_on_hand"),
            func.coalesce(func.sum(InventoryPosition.qty_reserved), 0).label("qty_reserved"),
            func.coalesce(func.sum(InventoryPosition.qty_in_transit), 0).label("qty_in_transit"),
        )
        .outerjoin(InventoryPosition, InventoryPosition.product_id == Product.id)
        .where(Product.tenant_id == tid)
        .group_by(
            Product.id,
            Product.name,
            Product.internal_ref,
            Product.erp_source_id,
            Product.uom,
            Product.source_type,
        )
        .order_by(Product.name)
    )
    if not include_purchased:
        stmt = stmt.where(Product.source_type == "manufactured")

    rows = (await session.execute(stmt)).all()
    items = []
    for row in rows:
        on_hand = float(row.qty_on_hand or 0)
        reserved = float(row.qty_reserved or 0)
        items.append(
            {
                "product_id": str(row.id),
                "name": row.name,
                "internal_ref": row.internal_ref,
                "erp_source_id": row.erp_source_id,
                "uom": row.uom or "unit",
                "source_type": row.source_type,
                "qty_on_hand": round(on_hand, 2),
                "qty_reserved": round(reserved, 2),
                "qty_in_transit": round(float(row.qty_in_transit or 0), 2),
                "qty_available": round(max(0, on_hand - reserved), 2),
            }
        )

    return APIResponse(
        success=True,
        data={"items": items, "total_products": len(items), "category": "all" if include_purchased else "finished_goods"},
        error=None,
    )


@router.post("/check-availability")
async def check_material_availability(
    req: AvailabilityRequest,
    current_user=Depends(require_roles(["admin", "planner"])),
    session: AsyncSession = Depends(get_db_session),
):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})
    try:
        required_date = datetime.fromisoformat(req.required_date)
    except ValueError:
        return APIResponse(success=False, data=None, error={"code": "INVALID_DATE", "message": "Invalid date format"})
    result = await rule_based_atp(
        session, UUID(tenant_id), req.product_id, req.quantity, required_date
    )

    await kafka_producer.send_event(
        "inventory", "changed",
        key=str(req.product_id),
        value=EventEnvelope(
            event_id=str(uuid4()),
            event_type="ipe.inventory.changed",
            source="mat-svc",
            tenant_id=UUID(tenant_id),
            timestamp=datetime.now(UTC),
            data={
                "product_id": str(req.product_id),
                "quantity": req.quantity,
                "required_date": req.required_date,
                "availability_p90": 1.0 if result.get("is_available") else 0.0,
                "is_available": result.get("is_available", False),
            },
        ).model_dump(mode="json"),
    )

    return APIResponse(success=True, data=result, error=None)


@router.post("/netting")
async def material_netting(
    req: NettingRequest,
    current_user=Depends(require_roles(["admin", "planner"])),
    session: AsyncSession = Depends(get_db_session),
):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})
    required_date = datetime.fromisoformat(req.required_date) if req.required_date else None
    result = await cumulative_netting(
        session, UUID(tenant_id), req.product_id, req.quantity, required_date
    )
    return APIResponse(success=True, data=result, error=None)


@router.post("/priority-netting")
async def material_priority_netting(
    req: PriorityNettingRequest,
    current_user=Depends(require_roles(["admin", "planner"])),
    session: AsyncSession = Depends(get_db_session),
):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})
    result = await priority_weighted_netting(
        session,
        UUID(tenant_id),
        req.product_id,
        req.demands,
        time_bucket_days=req.time_bucket_days,
    )
    return APIResponse(success=True, data=result, error=None)


@router.post("/check-availability-rule")
async def check_material_availability_rule(
    req: RuleBasedAtpRequest,
    current_user=Depends(require_roles(["admin", "planner"])),
    session: AsyncSession = Depends(get_db_session),
):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})
    try:
        required_date = datetime.fromisoformat(req.required_date)
    except ValueError:
        return APIResponse(success=False, data=None, error={"code": "INVALID_DATE", "message": "Invalid date format"})
    result = await rule_based_atp(
        session,
        UUID(tenant_id),
        req.product_id,
        req.quantity,
        required_date,
        delay_buffer_days=req.delay_buffer_days,
    )
    return APIResponse(success=True, data=result, error=None)


@router.post("/probabilistic-atp")
async def check_probabilistic_atp(
    req: ProbabilisticAtpRequest,
    current_user=Depends(require_roles(["admin", "planner"])),
    session: AsyncSession = Depends(get_db_session),
):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})
    try:
        required_start = datetime.fromisoformat(req.required_start)
    except ValueError:
        return APIResponse(success=False, data=None, error={"code": "INVALID_DATE", "message": "Invalid date format"})
    result = await probabilistic_atp(
        session,
        UUID(tenant_id),
        req.mo,
        req.components,
        req.priority_queue,
        required_start,
        num_simulations=req.num_simulations,
    )

    primary_material_id = result.get("bottleneck_component_id") or (
        req.components[0].get("component_id") if req.components else None
    )
    if primary_material_id:
        tlc = await compute_landed_cost(session, UUID(tenant_id), UUID(str(primary_material_id)))
        result["landed_cost_per_unit"] = tlc.get("landed_cost_per_unit", 0.0)
        result["landed_cost_breakdown"] = tlc.get("landed_cost_breakdown", {})
        result["material_attributes"] = tlc.get("material_attributes", {})
        for cr in result.get("component_breakdown", []):
            comp_tlc = await compute_landed_cost(
                session, UUID(tenant_id), UUID(str(cr["component_id"]))
            )
            cr["landed_cost_per_unit"] = comp_tlc.get("landed_cost_per_unit", 0.0)
            cr["landed_cost_breakdown"] = comp_tlc.get("landed_cost_breakdown", {})
            cr["material_attributes"] = comp_tlc.get("material_attributes", {})

    result["xai_explanation"] = XAIExplanation(
        constraints=["monte_carlo_simulation", f"num_simulations_{req.num_simulations}"]
                     + ([f"bottleneck_component_{result.get('bottleneck_component_id', '')}"] if result.get("bottleneck_component_id") else []),
        assumptions=["demand_forecast_stable", "supplier_lead_time_distribution"],
        confidence_score=round(result.get("overall_confidence", 0.0), 4),
        contributing_factors={cr["component_id"]: round(cr["confidence"], 4) for cr in result.get("component_breakdown", [])[:5]} if result.get("component_breakdown") else {"overall_confidence": round(result.get("overall_confidence", 0.0), 4)},
    ).model_dump()

    return APIResponse(success=True, data=result, error=None)


@router.post("/supplier-predict")
async def supplier_delay_prediction(
    req: SupplierPredictRequest,
    current_user=Depends(require_roles(["admin", "planner"])),
    session: AsyncSession = Depends(get_db_session),
):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})

    from sqlalchemy import select as sa_select

    from ipe_shared.models.supplier import Supplier

    if req.supplier_id:
        result = await session.execute(
            sa_select(Supplier).where(
                Supplier.tenant_id == UUID(tenant_id),
                Supplier.id == req.supplier_id,
            )
        )
        supplier = result.scalar_one_or_none()
        if not supplier:
            return APIResponse(success=False, data=None, error={"code": "NOT_FOUND", "message": "Supplier not found"})
        suppliers = [supplier]
    else:
        result = await session.execute(
            sa_select(Supplier).where(Supplier.tenant_id == UUID(tenant_id))
        )
        suppliers = list(result.scalars().all())

    predictions = []
    for s in suppliers:
        pred = predict_delay(
            avg_delay_days=s.avg_delay_days,
            delay_std_dev_days=s.delay_std_dev_days,
            reliability_score=s.reliability_score,
            distribution_type=s.delay_distribution_type or "normal",
            distribution_params=s.delay_distribution_params,
        )
        predictions.append({
            "supplier_id": str(s.id),
            "supplier_name": s.name,
            "reliability_score": float(s.reliability_score) if s.reliability_score else None,
            **pred,
        })

    return APIResponse(success=True, data={"predictions": predictions}, error=None)


@router.post("/safety-stock")
async def compute_safety_stock(
    req: SafetyStockRequest,
    current_user=Depends(require_roles(["admin", "planner"])),
    session: AsyncSession = Depends(get_db_session),
):
    """Calculate dynamic safety stock for a single product."""
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})

    if req.avg_daily_demand is not None:
        result = calculate_safety_stock(
            avg_daily_demand=req.avg_daily_demand,
            demand_std_dev=req.demand_std_dev or 0,
            avg_lead_time_days=req.avg_lead_time_days or 7,
            lead_time_std_dev=req.lead_time_std_dev or 1,
            service_level=req.service_level,
        )
        return APIResponse(success=True, data=result, error=None)

    if req.product_id:
        from sqlalchemy import select as sa_select
        from ipe_shared.models.inventory import InventoryPosition
        from ipe_shared.models.supplier import Supplier
        from ipe_shared.models.supply import SupplyOrder

        tid = UUID(tenant_id)

        inv_result = await session.execute(
            sa_select(InventoryPosition)
            .where(InventoryPosition.tenant_id == tid)
            .where(InventoryPosition.product_id == req.product_id)
            .order_by(InventoryPosition.time.desc())
            .limit(1)
        )
        inv = inv_result.scalar_one_or_none()

        supply_result = await session.execute(
            sa_select(SupplyOrder, Supplier)
            .outerjoin(Supplier, SupplyOrder.supplier_id == Supplier.id)
            .where(SupplyOrder.tenant_id == tid)
            .where(SupplyOrder.product_id == req.product_id)
            .where(SupplyOrder.status.in_(["confirmed", "in_transit"]))
        )
        supply_rows = list(supply_result.all())

        avg_daily = 0.0
        demand_std = 0.0
        lt_days = 7.0
        lt_std = 1.0

        if supply_rows:
            quantities = [float(s.quantity_ordered or 0) for s, _ in supply_rows]
            avg_daily = sum(quantities) / max(1, len(quantities))
            if len(quantities) > 1:
                mean_q = avg_daily
                demand_std = math.sqrt(sum((q - mean_q) ** 2 for q in quantities) / (len(quantities) - 1))

            for _, supplier in supply_rows:
                if supplier and supplier.avg_delay_days:
                    lt_days = float(supplier.avg_delay_days)
                    lt_std = float(supplier.delay_std_dev_days or 1)
                    break

        result = calculate_safety_stock(
            avg_daily_demand=avg_daily,
            demand_std_dev=demand_std,
            avg_lead_time_days=lt_days,
            lead_time_std_dev=lt_std,
            service_level=req.service_level,
        )
        return APIResponse(success=True, data=result, error=None)

    return APIResponse(success=False, data=None, error={"code": "MISSING_PARAMS", "message": "Provide product_id or demand parameters"})


@router.post("/safety-stock/bulk")
async def compute_bulk_safety_stock(
    req: BulkSafetyStockRequest,
    current_user=Depends(require_roles(["admin", "planner"])),
    session: AsyncSession = Depends(get_db_session),
):
    """Calculate safety stock for multiple products at once."""
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})

    results = calculate_all_products_safety_stock(
        products=req.products,
        service_level=req.service_level,
    )
    return APIResponse(success=True, data={"safety_stock": results}, error=None)


@router.post("/po-suggestions")
async def suggest_purchase_orders(
    req: POSuggestionRequest,
    current_user=Depends(require_roles(["admin", "planner"])),
    session: AsyncSession = Depends(get_db_session),
):
    """Generate PO suggestions from shortage data."""
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})

    suggestions = generate_po_suggestions(
        shortages=req.shortages,
        suppliers=req.suppliers,
        service_level=req.service_level,
        holding_cost_pct=req.holding_cost_pct,
        order_cost=req.order_cost,
    )

    if req.merge:
        suggestions = merge_po_suggestions(suggestions)

    total_cost = sum(s.get("total_cost", 0) for s in suggestions)

    if suggestions:
        try:
            envelope = kafka_producer.build_envelope(
                event_type="ipe.po.suggested",
                tenant_id=UUID(tenant_id),
                payload={
                    "suggestion_count": len(suggestions),
                    "total_cost": total_cost,
                    "suggestions": suggestions,
                },
            )
            await kafka_producer.send_avro(
                topic="ipe.po.suggested",
                key=str(UUID(tenant_id)),
                envelope=envelope,
            )
        except Exception:
            logger.warning("Failed to publish ipe.po.suggested event (Kafka unavailable)")

    return APIResponse(
        success=True,
        data={
            "suggestions": suggestions,
            "total_suggestions": len(suggestions),
            "total_cost": round(total_cost, 2),
        },
        error=None,
    )


class CTPRequest(BaseModel):
    order_id: UUID
    product_id: UUID
    quantity: int
    required_date: str
    priority_score: float = 0.5
    penalty_cost: float = 100.0
    duration_mins_per_unit: float = 60.0


class CTPBatchRequest(BaseModel):
    orders: list[CTPRequest]
    duration_mins_per_unit: float = 60.0


@router.post("/ctp")
async def capable_to_promise(
    req: CTPRequest,
    current_user=Depends(require_roles(["admin", "planner"])),
    session: AsyncSession = Depends(get_db_session),
):
    """Real-time Capable-to-Promise: check material + capacity feasibility."""
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})

    tid = UUID(tenant_id)

    from sqlalchemy import select as sa_select
    from ipe_shared.models.inventory import InventoryPosition
    from ipe_shared.models.supply import SupplyOrder
    from ipe_shared.models.work_center import WorkCenter

    inv_result = await session.execute(
        sa_select(InventoryPosition).where(InventoryPosition.tenant_id == tid)
    )
    inventory = inv_result.scalars().all()

    supply_result = await session.execute(
        sa_select(SupplyOrder).where(
            SupplyOrder.tenant_id == tid,
            SupplyOrder.product_id == req.product_id,
            SupplyOrder.status.in_(["confirmed", "in_transit"]),
        )
    )
    supplies = supply_result.scalars().all()

    wc_result = await session.execute(
        sa_select(WorkCenter).where(WorkCenter.tenant_id == tid)
    )
    work_centers = wc_result.scalars().all()

    inv_map = {str(i.product_id): float(i.qty_on_hand or 0) for i in inventory}
    available = inv_map.get(str(req.product_id), 0)

    for supply in supplies:
        available += float(supply.quantity_ordered or 0)

    materials = [
        MaterialAvailability(
            product_id=str(req.product_id),
            quantity_available=available,
            quantity_required=float(req.quantity),
            lead_time_days=7,
        )
    ]

    capacity_slots = []
    for wc in work_centers:
        for day_offset in range(30):
            capacity_slots.append(CapacitySlot(
                work_center_id=str(wc.id),
                date=f"day_{day_offset}",
                available_hours=float(wc.capacity_hours_per_day or 8),
            ))

    order = CTPOrderLine(
        order_id=str(req.order_id),
        product_id=str(req.product_id),
        quantity=req.quantity,
        required_date=req.required_date,
        priority_score=req.priority_score,
        penalty_cost=req.penalty_cost,
    )

    result = solve_ctp(
        orders=[order],
        materials=materials,
        capacity_slots=capacity_slots,
        duration_mins_per_unit=req.duration_mins_per_unit,
    )

    ctp_result = result[0] if result else None

    return APIResponse(success=True, data={
        "order_id": str(req.order_id),
        "earliest_delivery_date": ctp_result.earliest_delivery_date if ctp_result else req.required_date,
        "feasible": ctp_result.feasible if ctp_result else False,
        "confidence_score": ctp_result.confidence_score if ctp_result else 0.0,
        "material_feasible": ctp_result.material_feasible if ctp_result else False,
        "capacity_feasible": ctp_result.capacity_feasible if ctp_result else False,
        "bottleneck": ctp_result.bottleneck if ctp_result else None,
        "material_gaps": ctp_result.material_gaps if ctp_result else [],
        "capacity_gaps": ctp_result.capacity_gaps if ctp_result else [],
        "fallback_used": ctp_result.fallback_used if ctp_result else False,
        "solve_time_ms": ctp_result.solve_time_ms if ctp_result else 0.0,
        "xai_explanation": XAIExplanation(
            constraints=["material_availability", "capacity_slot_availability"]
                         + ([ctp_result.bottleneck] if ctp_result and ctp_result.bottleneck else []),
            assumptions=["30_day_capacity_horizon", "7_day_lead_time_default"]
                         + (["fallback_solver_used"] if ctp_result and ctp_result.fallback_used else []),
            confidence_score=round(ctp_result.confidence_score if ctp_result else 0.0, 4),
            contributing_factors={
                "material": round(1.0 if ctp_result and ctp_result.material_feasible else 0.0, 4),
                "capacity": round(1.0 if ctp_result and ctp_result.capacity_feasible else 0.0, 4),
            },
        ).model_dump(),
    }, error=None)


@router.post("/ctp/batch")
async def capable_to_promise_batch(
    req: CTPBatchRequest,
    current_user=Depends(require_roles(["admin", "planner"])),
    session: AsyncSession = Depends(get_db_session),
):
    """Batch CTP: check multiple orders at once."""
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})

    tid = UUID(tenant_id)

    from sqlalchemy import select as sa_select
    from ipe_shared.models.inventory import InventoryPosition
    from ipe_shared.models.supply import SupplyOrder
    from ipe_shared.models.work_center import WorkCenter

    inv_result = await session.execute(
        sa_select(InventoryPosition).where(InventoryPosition.tenant_id == tid)
    )
    inventory = inv_result.scalars().all()

    wc_result = await session.execute(
        sa_select(WorkCenter).where(WorkCenter.tenant_id == tid)
    )
    work_centers = wc_result.scalars().all()

    inv_map = {str(i.product_id): float(i.qty_on_hand or 0) for i in inventory}

    orders = []
    for o in req.orders:
        available = inv_map.get(str(o.product_id), 0)
        materials = [
            MaterialAvailability(
                product_id=str(o.product_id),
                quantity_available=available,
                quantity_required=float(o.quantity),
                lead_time_days=7,
            )
        ]
        orders.append(CTPOrderLine(
            order_id=str(o.order_id),
            product_id=str(o.product_id),
            quantity=o.quantity,
            required_date=o.required_date,
            priority_score=o.priority_score,
            penalty_cost=o.penalty_cost,
        ))

    capacity_slots = []
    for wc in work_centers:
        for day_offset in range(30):
            capacity_slots.append(CapacitySlot(
                work_center_id=str(wc.id),
                date=f"day_{day_offset}",
                available_hours=float(wc.capacity_hours_per_day or 8),
            ))

    results = solve_ctp(
        orders=orders,
        materials=[MaterialAvailability(
            product_id=str(o.product_id),
            quantity_available=inv_map.get(str(o.product_id), 0),
            quantity_required=float(o.quantity),
            lead_time_days=7,
        ) for o in req.orders],
        capacity_slots=capacity_slots,
        duration_mins_per_unit=req.duration_mins_per_unit,
    )

    return APIResponse(success=True, data={
        "results": [
            {
                "order_id": r.order_id,
                "earliest_delivery_date": r.earliest_delivery_date,
                "feasible": r.feasible,
                "confidence_score": r.confidence_score,
                "bottleneck": r.bottleneck,
                "solve_time_ms": r.solve_time_ms,
            }
            for r in results
        ],
        "total_orders": len(results),
        "feasible_count": sum(1 for r in results if r.feasible),
        "xai_explanation": XAIExplanation(
            constraints=["material_availability", "capacity_slot_availability", "batch_processing"],
            assumptions=["30_day_capacity_horizon", "7_day_lead_time_default"],
            confidence_score=round(sum(r.confidence_score for r in results) / max(1, len(results)), 4),
            contributing_factors={
                "feasible_ratio": round(sum(1 for r in results if r.feasible) / max(1, len(results)), 4),
                "avg_confidence": round(sum(r.confidence_score for r in results) / max(1, len(results)), 4),
            },
        ).model_dump(),
    }, error=None)
