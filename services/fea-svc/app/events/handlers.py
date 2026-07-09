from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.core.scorer import _compute_capacity_gate, _compute_labor_gate, calculate_feasibility
from ipe_shared.activity.emit import record_from_kafka_topic
from ipe_shared.database.connection import get_engine
from ipe_shared.events.producer import kafka_producer
from ipe_shared.middleware.tenant_context import tenant_ctx


async def _score_and_publish(session, mo_id: str, tenant_id: str, mat_score: float | None, cap_score: float | None):
    """Score and publish if both gates have arrived; otherwise skip."""
    if mat_score is None or cap_score is None:
        return

    mo_row = (
        await session.execute(
            text("""
                SELECT status, product_id FROM cdm_manufacturing_order
                WHERE id = :mo_id AND tenant_id = :tenant_id
            """),
            {"mo_id": UUID(mo_id), "tenant_id": UUID(tenant_id)},
        )
    ).one_or_none()
    if not mo_row:
        return

    status, product_id = mo_row
    demand_score = 100.0 if status != "draft" else 50.0

    bom_exists = (
        await session.execute(
            text("SELECT 1 FROM cdm_bill_of_material WHERE product_id = :pid AND is_active = true LIMIT 1"),
            {"pid": product_id},
        )
    ).scalar_one_or_none()
    bom_score = 100.0 if bom_exists else 50.0

    cap_gate = await _compute_capacity_gate(mo_id, tenant_id, session)
    lab_gate = await _compute_labor_gate(mo_id, tenant_id, session)

    result = calculate_feasibility(
        demand_score=demand_score,
        bom_score=bom_score,
        material_score=mat_score,
        capacity_score=cap_gate,
        labor_score=lab_gate,
        autonomy_mode="shadow",
    )

    await session.execute(
        text("""
            UPDATE cdm_manufacturing_order
            SET feasibility_score = :fs, primary_constraint = :pc, autonomy_action = :aa,
                capacity_score = :cs, labor_score = :ls
            WHERE id = :mo_id
        """),
        {
            "fs": result["feasibility_score"],
            "pc": result["primary_constraint"],
            "aa": result["action_taken"],
            "cs": cap_gate,
            "ls": lab_gate,
            "mo_id": UUID(mo_id),
        },
    )
    await session.commit()

    envelope = kafka_producer.build_envelope(
        event_type="ipe.mo.feasibility_scored",
        tenant_id=tenant_id,
        payload={
            "mo_id": str(mo_id),
            "feasibility_score": result["feasibility_score"],
            "primary_constraint": result["primary_constraint"],
            "action": result["action_taken"],
        },
    )
    await kafka_producer.send_avro(
        topic="ipe.mo.feasibility_scored",
        key=str(mo_id),
        envelope=envelope,
    )

    await record_from_kafka_topic(
        session,
        "ipe.feasibility.scored",
        envelope,
        tenant_id=tenant_id,
    )


async def _get_avro_payload(event: dict) -> dict:
    """Extract the inner payload from an event dict (supports both Avro-envelope and raw)."""
    if isinstance(event, dict) and "payload" in event:
        return event["payload"]
    return event.get("data", event)


async def handle_material_scored(event: dict):
    payload = await _get_avro_payload(event)
    mo_id = payload.get("mo_id")
    tenant_id = tenant_ctx.get()
    if not mo_id or not tenant_id:
        return

    mat_score = payload.get("material_score") or payload.get("confidence")
    if mat_score is None:
        return

    engine = get_engine()
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        # Read current capacity_score from DB (may have arrived earlier or later)
        row = (
            await session.execute(
                text("SELECT capacity_score FROM cdm_manufacturing_order WHERE id = :mo_id"),
                {"mo_id": UUID(mo_id)},
            )
        ).scalar_one_or_none()
        cap_score = float(row) if row is not None else None
        await _score_and_publish(session, str(mo_id), tenant_id, float(mat_score), cap_score)


async def handle_capacity_scored(event: dict):
    payload = await _get_avro_payload(event)
    mo_id = payload.get("mo_id")
    tenant_id = tenant_ctx.get()
    if not mo_id or not tenant_id:
        return

    cap_score = payload.get("capacity_score")
    if cap_score is None:
        return

    # Map solver status to score: INFEASIBLE->0, on-time->100, else 50
    solver_status = payload.get("solver_status", "UNKNOWN")
    if solver_status == "INFEASIBLE":
        cap_score = 0.0
    elif solver_status == "OPTIMAL":
        cap_score = 100.0
    else:
        cap_score = 50.0

    engine = get_engine()
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        # Write capacity_score to MO
        await session.execute(
            text("""
                UPDATE cdm_manufacturing_order
                SET capacity_score = :cs
                WHERE id = :mo_id
            """),
            {"cs": cap_score, "mo_id": UUID(mo_id)},
        )
        await session.commit()

        # Read current material_score
        row = (
            await session.execute(
                text("SELECT material_score FROM cdm_manufacturing_order WHERE id = :mo_id"),
                {"mo_id": UUID(mo_id)},
            )
        ).scalar_one_or_none()
        mat_score = float(row) if row is not None else None
        await _score_and_publish(session, str(mo_id), tenant_id, mat_score, cap_score)
