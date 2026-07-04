from sqlalchemy import select as sa_select
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.core.priority import compute_priority_score
from ipe_shared.database.connection import get_engine
from ipe_shared.events.producer import kafka_producer
from ipe_shared.middleware.tenant_context import tenant_ctx
from ipe_shared.models.bom import BillOfMaterial
from ipe_shared.models.demand import DemandLine
from ipe_shared.models.manufacturing_order import ManufacturingOrder
from ipe_shared.models.product import Product
from ipe_shared.tenant.quotas import count_tenant_resource, enforce_quota


async def handle_demand_created(event: dict):
    demand_line_id = event.get("demand_line_id")
    if not demand_line_id:
        return

    engine = get_engine()
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        tid = tenant_ctx.get()
        if tid:
            await session.execute(
                text("SELECT set_config('app.current_tenant_id', :tid, false)"),
                {"tid": str(tid)},
            )

        result = await session.execute(
            sa_select(DemandLine, Product)
            .join(Product, DemandLine.product_id == Product.id)
            .where(DemandLine.id == demand_line_id)
        )
        row = result.one_or_none()
        if not row:
            return

        demand_line, product = row

        dl_dict = {
            "customer_tier": int(demand_line.customer_tier) if demand_line.customer_tier else 3,
            "margin_pct": float(demand_line.margin_pct) if demand_line.margin_pct else 0,
            "required_date": demand_line.required_date,
            "penalty_cost": float(demand_line.penalty_cost) if demand_line.penalty_cost else 0,
            "tags": product.category_tags or [],
        }

        priority = compute_priority_score(dl_dict)
        priority_score = priority["priority_score"]

        demand_line.priority_score = priority_score

        if demand_line.mo_id:
            mo_id = demand_line.mo_id
        else:
            bom_result = await session.execute(
                sa_select(BillOfMaterial.id)
                .where(
                    BillOfMaterial.product_id == demand_line.product_id,
                    BillOfMaterial.is_active,
                )
                .order_by(BillOfMaterial.version.desc())
                .limit(1)
            )
            bom_row = bom_result.fetchone()
            bom_id = bom_row[0] if bom_row else None

            if bom_id:
                if not tid:
                    mo_id = None
                else:
                    mo_count = await count_tenant_resource(session, tid, "manufacturing_orders")
                    await enforce_quota(str(tid), "manufacturing_orders", mo_count)
                    mo = ManufacturingOrder(
                        tenant_id=tid,
                        product_id=demand_line.product_id,
                        bom_id=bom_id,
                        quantity=demand_line.quantity,
                        status="draft",
                    )
                    session.add(mo)
                    await session.flush()
                    mo_id = mo.id
                    demand_line.mo_id = mo_id
            else:
                mo_id = None

        await session.commit()

        envelope = kafka_producer.build_envelope(
            event_type="ipe.demand.classified",
            tenant_id=str(tid) if tid else "unknown",
            payload={
                "demand_line_id": str(demand_line_id),
                "mo_id": str(mo_id) if mo_id else "",
                "priority_score": float(priority_score),
            },
        )

        await kafka_producer.send_avro(
            topic="ipe.demand.classified",
            key=str(demand_line_id),
            envelope=envelope,
        )


async def handle_inventory_changed(event: dict):
    """Re-score demand when inventory changes.

    When material availability changes, demand priorities may need
    recalculation. This handler re-evaluates demand lines that reference
    the affected product and emits updated priority scores.
    """
    product_id = event.get("product_id")
    if not product_id:
        return

    engine = get_engine()
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        tid = tenant_ctx.get()
        if tid:
            from sqlalchemy import text
            await session.execute(
                text("SELECT set_config('app.current_tenant_id', :tid, false)"),
                {"tid": str(tid)},
            )

        from uuid import UUID as _UUID
        try:
            pid = _UUID(product_id)
        except (ValueError, TypeError):
            return

        result = await session.execute(
            sa_select(DemandLine, Product)
            .join(Product, DemandLine.product_id == Product.id)
            .where(DemandLine.product_id == pid)
        )
        rows = result.all()

        for demand_line, product in rows:
            dl_dict = {
                "customer_tier": int(demand_line.customer_tier) if demand_line.customer_tier else 3,
                "margin_pct": float(demand_line.margin_pct) if demand_line.margin_pct else 0,
                "required_date": demand_line.required_date,
                "penalty_cost": float(demand_line.penalty_cost) if demand_line.penalty_cost else 0,
                "tags": product.category_tags or [],
            }
            priority = compute_priority_score(dl_dict)
            demand_line.priority_score = priority["priority_score"]

        await session.commit()
