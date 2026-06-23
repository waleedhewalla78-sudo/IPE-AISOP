import math
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

G1_DEMAND_WEIGHT = 0.05
G2_BOM_WEIGHT = 0.05
G3_MATERIAL_WEIGHT = 0.35
G4_CAPACITY_WEIGHT = 0.30
G5_LABOR_WEIGHT = 0.25


def _resolve(v: float | None, default: float) -> float:
    if v is None or math.isnan(v) or math.isinf(v):
        return default
    return v


async def _compute_capacity_gate(mo_id: str, tenant_id: str, session: AsyncSession) -> float:
    wc_rows = (
        await session.execute(
            text("""
                SELECT DISTINCT ro.work_center_id
                FROM cdm_manufacturing_order mo
                JOIN cdm_routing_operation ro ON ro.bom_id = mo.bom_id
                WHERE mo.id = :mo_id AND mo.tenant_id = :tenant_id
            """),
            {"mo_id": UUID(mo_id), "tenant_id": UUID(tenant_id)},
        )
    ).fetchall()

    if not wc_rows:
        return 100.0

    max_utilization = 0.0
    for (wc_id,) in wc_rows:
        sched_result = await session.execute(
            text("""
                SELECT COALESCE(SUM(wo.duration_planned_mins), 0)
                FROM cdm_work_order wo
                WHERE wo.work_center_id = :wc_id
            """),
            {"wc_id": wc_id},
        )
        scheduled_mins = float(sched_result.scalar() or 0)

        wc_row = (
            await session.execute(
                text("SELECT capacity_hours_per_day, oee FROM cdm_work_center WHERE id = :wc_id"),
                {"wc_id": wc_id},
            )
        ).one_or_none()

        if not wc_row or wc_row[0] is None:
            continue

        oee = float(wc_row[1]) if wc_row[1] is not None else 0.85
        available_mins = float(wc_row[0]) * 60.0 * oee

        if available_mins == 0:
            continue

        utilization = scheduled_mins / available_mins
        max_utilization = max(max_utilization, utilization)

    if max_utilization == 0.0:
        return 100.0

    score = 100.0 - (max_utilization - 0.85) * 200.0
    return max(0.0, min(100.0, score))


async def _compute_labor_gate(mo_id: str, tenant_id: str, session: AsyncSession) -> float:
    wc_rows = (
        await session.execute(
            text("""
                SELECT DISTINCT ro.work_center_id
                FROM cdm_manufacturing_order mo
                JOIN cdm_routing_operation ro ON ro.bom_id = mo.bom_id
                WHERE mo.id = :mo_id AND mo.tenant_id = :tenant_id
            """),
            {"mo_id": UUID(mo_id), "tenant_id": UUID(tenant_id)},
        )
    ).fetchall()

    if not wc_rows:
        return 100.0

    wc_ids = [row[0] for row in wc_rows]

    op_rows = (
        await session.execute(
            text("""
                SELECT DISTINCT wo.operator_id
                FROM cdm_work_order wo
                WHERE wo.work_center_id = ANY(:wc_ids)
                  AND wo.operator_id IS NOT NULL
            """),
            {"wc_ids": wc_ids},
        )
    ).fetchall()

    if not op_rows:
        return 100.0

    op_ids = [row[0] for row in op_rows]

    abs_rows = (
        await session.execute(
            text("""
                SELECT predicted_absence_probability
                FROM cdm_operator
                WHERE id = ANY(:op_ids)
                  AND predicted_absence_probability IS NOT NULL
            """),
            {"op_ids": op_ids},
        )
    ).fetchall()

    if not abs_rows:
        return 100.0

    max_absence = max(float(r[0]) for r in abs_rows)
    score = 100.0 * (1.0 - max_absence)
    return max(0.0, min(100.0, score))


def calculate_feasibility(
    demand_score: float | None = None,
    bom_score: float | None = None,
    material_score: float | None = None,
    capacity_score: float | None = None,
    labor_score: float | None = None,
    autonomy_mode: str = "shadow",
) -> dict:
    demand_score = _resolve(demand_score, 100.0)
    bom_score = _resolve(bom_score, 100.0)
    material_score = _resolve(material_score, 50.0)
    capacity_score = _resolve(capacity_score, 50.0)
    labor_score = _resolve(labor_score, 50.0)

    def clamp(v: float) -> float:
        return max(0.0, min(100.0, v))

    g1 = clamp(demand_score)
    g2 = clamp(bom_score)
    g3 = clamp(material_score)
    g4 = clamp(capacity_score)
    g5 = clamp(labor_score)

    composite = (
        g1 * G1_DEMAND_WEIGHT
        + g2 * G2_BOM_WEIGHT
        + g3 * G3_MATERIAL_WEIGHT
        + g4 * G4_CAPACITY_WEIGHT
        + g5 * G5_LABOR_WEIGHT
    )

    score_rounded = round(composite, 2)

    gate_scores = {
        "demand": round(g1, 2),
        "bom": round(g2, 2),
        "material": round(g3, 2),
        "capacity": round(g4, 2),
        "labor": round(g5, 2),
    }

    real_gates = [("demand", g1), ("bom", g2), ("material", g3), ("capacity", g4), ("labor", g5)]
    real_gates.sort(key=lambda x: x[1])
    primary_constraint = real_gates[0][0] if real_gates and real_gates[0][1] < 100.0 else "none"

    if autonomy_mode == "autonomous" and score_rounded >= 90.0:
        action_taken = "auto_confirmed"
    elif score_rounded >= 70.0:
        action_taken = "queued_for_planner"
    else:
        action_taken = "routed_to_resolution"

    return {
        "feasibility_score": score_rounded,
        "gate_scores": gate_scores,
        "primary_constraint": primary_constraint,
        "action_taken": action_taken,
        "is_feasible": score_rounded >= 50.0,
        "risk_level": (
            "low" if score_rounded >= 80.0 else "medium" if score_rounded >= 50.0 else "high"
        ),
    }


async def score_from_mo(
    tenant_id: str,
    mo_id: str,
    session: AsyncSession | None = None,
    autonomy_mode: str = "shadow",
) -> dict:
    cap_score = 100.0
    lab_score = 100.0

    if session is None:
        return calculate_feasibility(
            capacity_score=cap_score,
            labor_score=lab_score,
            autonomy_mode=autonomy_mode,
        )

    row = (
        await session.execute(
            text("""
            SELECT status, material_score, capacity_score, labor_score, product_id
            FROM cdm_manufacturing_order
            WHERE id = :mo_id AND tenant_id = :tenant_id
        """),
            {"mo_id": UUID(mo_id), "tenant_id": UUID(tenant_id)},
        )
    ).one_or_none()

    if row is None:
        return {
            "error": "MO not found",
            "feasibility_score": 0,
            "primary_constraint": None,
            "action_taken": "routed_to_resolution",
        }

    status, material_score, _cap_score, _lab_score, product_id = row

    demand_score = 100.0 if status != "draft" else 50.0

    bom_exists = (
        await session.execute(
            text(
                "SELECT 1 FROM cdm_bill_of_material"
                " WHERE product_id = :pid AND is_active = true LIMIT 1"
            ),
            {"pid": product_id},
        )
    ).scalar_one_or_none()
    bom_score = 100.0 if bom_exists else 50.0

    mat_score = float(material_score) if material_score is not None else None

    cap_score = await _compute_capacity_gate(mo_id, tenant_id, session)
    lab_score = await _compute_labor_gate(mo_id, tenant_id, session)

    result = calculate_feasibility(
        demand_score=demand_score,
        bom_score=bom_score,
        material_score=mat_score,
        capacity_score=cap_score,
        labor_score=lab_score,
        autonomy_mode=autonomy_mode,
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
            "cs": cap_score,
            "ls": lab_score,
            "mo_id": UUID(mo_id),
        },
    )
    await session.commit()

    return result