import logging
from datetime import UTC, datetime

from sqlalchemy import select as sa_select
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.core.reconciliation import analyze_mo_completion
from ipe_shared.database.connection import get_engine
from ipe_shared.events.producer import kafka_producer
from ipe_shared.middleware.tenant_context import tenant_ctx
from ipe_shared.models.manufacturing_order import ManufacturingOrder
from ipe_shared.models.work_order import WorkOrder

logger = logging.getLogger(__name__)


async def handle_mo_completed(event: dict):
    """Handle MO completed events by running reconciliation analysis.

    Compares planned vs actual duration, yield, and scrap to produce
    a reconciliation summary. Emits ipe.reconciliation.completed.
    """
    mo_id = event.get("mo_id")
    if not mo_id:
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

        result = await session.execute(
            sa_select(ManufacturingOrder).where(ManufacturingOrder.id == mo_id)
        )
        mo = result.scalar_one_or_none()
        if mo is None:
            logger.warning("handle_mo_completed: MO %s not found", mo_id)
            return

        wo_result = await session.execute(
            sa_select(WorkOrder).where(WorkOrder.mo_id == mo_id)
        )
        work_orders = list(wo_result.scalars().all())

        analysis = analyze_mo_completion(mo, work_orders)

    envelope = kafka_producer.build_envelope(
        event_type="ipe.reconciliation.completed",
        tenant_id=str(tid) if tid else "unknown",
        payload=analysis,
    )
    await kafka_producer.send_avro(
        topic="ipe.reconciliation.completed",
        key=str(mo_id),
        envelope=envelope,
    )
