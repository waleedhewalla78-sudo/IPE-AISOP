from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auto_confirm import should_auto_confirm
from app.core.scorer import calculate_feasibility, score_from_mo
from ipe_shared.audit.service import log_audit_event
from ipe_shared.auth.jwt import TokenPayload
from ipe_shared.auth.rbac import require_roles
from ipe_shared.database.session import get_session as get_db_session
from ipe_shared.events.producer import kafka_producer
from ipe_shared.events.schemas import EventEnvelope
from ipe_shared.middleware.tenant_context import tenant_ctx
from ipe_shared.mdr.engine import calculate_mdr, format_mdr_response
from ipe_shared.schemas.common import APIResponse
from ipe_shared.schemas.xai import XAIExplanation

router = APIRouter(prefix="/feasibility", tags=["feasibility"])


class ScoreRequest(BaseModel):
    mo_id: UUID
    demand_score: float | None = None
    bom_score: float | None = None
    material_score: float | None = None
    capacity_score: float | None = None
    labor_score: float | None = None
    autonomy_mode: str = "shadow"


class AutoConfirmRequest(BaseModel):
    mo_id: UUID
    feasibility_score: float
    autonomy_mode: str = "shadow"
    primary_constraint: str | None = None


@router.get("/mdr")
async def get_mdr_score(
    session: AsyncSession = Depends(get_db_session),
    current_user: TokenPayload = Depends(require_roles(["admin", "planner", "manager", "auditor"])),
) -> APIResponse:
    """Master Data Readiness breakdown — composite score and per-dimension coverage."""
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(
            success=False,
            data=None,
            error={"code": "NO_TENANT", "message": "X-Tenant-ID required"},
        )
    result = await calculate_mdr(session, tenant_id=tenant_id)
    if result.get("error"):
        return APIResponse(
            success=False,
            data=None,
            error={"code": "MDR_ERROR", "message": result["error"]},
        )
    return APIResponse(success=True, data=format_mdr_response(tenant_id, result), error=None)


@router.post("/score")
async def score_feasibility(
    req: ScoreRequest,
    session: AsyncSession = Depends(get_db_session),
):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(
            success=False,
            data=None,
            error={"code": "NO_TENANT", "message": "No tenant context"},
        )
    result = calculate_feasibility(
        demand_score=req.demand_score,
        bom_score=req.bom_score,
        material_score=req.material_score,
        capacity_score=req.capacity_score,
        labor_score=req.labor_score,
        autonomy_mode=req.autonomy_mode,
    )

    await kafka_producer.send_event(
        "mo",
        "feasibility_scored",
        key=str(req.mo_id),
        value=EventEnvelope(
            event_id=str(uuid4()),
            event_type="ipe.mo.feasibility_scored",
            source="fea-svc",
            tenant_id=UUID(tenant_id),
            timestamp=datetime.now(UTC),
            data={
                "mo_id": str(req.mo_id),
                "overall_score": result["feasibility_score"],
                "gate_scores": result.get("gate_scores", {}),
                "action_taken": result.get("action_taken", ""),
                "primary_constraint": result.get("primary_constraint"),
                "risk_level": result.get("risk_level", "medium"),
            },
        ).model_dump(mode="json"),
    )

    xai = XAIExplanation(
        constraints=[result["primary_constraint"]] if result["primary_constraint"] != "none" else [],
        assumptions=["stable_demand_forecast" if result.get("gate_scores", {}).get("demand", 0) >= 80 else "volatile_demand"],
        confidence_score=round(result["feasibility_score"] / 100.0, 4),
        contributing_factors={
            "demand": round(result.get("gate_scores", {}).get("demand", 0) / 100.0 * 0.05, 4),
            "bom": round(result.get("gate_scores", {}).get("bom", 0) / 100.0 * 0.05, 4),
            "material": round(result.get("gate_scores", {}).get("material", 0) / 100.0 * 0.35, 4),
            "capacity": round(result.get("gate_scores", {}).get("capacity", 0) / 100.0 * 0.30, 4),
            "labor": round(result.get("gate_scores", {}).get("labor", 0) / 100.0 * 0.25, 4),
        },
    )
    result["xai_explanation"] = xai.model_dump()

    return APIResponse(success=True, data=result, error=None)


@router.post("/auto-confirm")
async def auto_confirm(
    req: AutoConfirmRequest,
    session: AsyncSession = Depends(get_db_session),
    current_user: TokenPayload = Depends(require_roles(["planner", "admin", "manager"])),
):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(
            success=False,
            data=None,
            error={"code": "NO_TENANT", "message": "No tenant context"},
        )
    result = should_auto_confirm(
        feasibility_score=req.feasibility_score,
        autonomy_mode=req.autonomy_mode,
        primary_constraint=req.primary_constraint,
    )

    result["xai_explanation"] = XAIExplanation(
        constraints=[req.primary_constraint] if req.primary_constraint else [],
        assumptions=[f"threshold_{req.autonomy_mode}_mode"],
        confidence_score=round(req.feasibility_score / 100.0, 4) if req.feasibility_score else 0.0,
        contributing_factors={"feasibility_score": round(req.feasibility_score / 100.0, 4) if req.feasibility_score else 0.0},
    ).model_dump()

    if result.get("should_confirm"):
        await kafka_producer.send_event(
            "mo",
            "auto_confirmed",
            key=str(req.mo_id),
            value=EventEnvelope(
                event_id=str(uuid4()),
                event_type="ipe.mo.auto_confirmed",
                source="fea-svc",
                tenant_id=UUID(tenant_id),
                timestamp=datetime.now(UTC),
                data={
                    "mo_id": str(req.mo_id),
                    "feasibility_score": req.feasibility_score,
                    "autonomy_mode": req.autonomy_mode,
                    "reason": result.get("reason", ""),
                },
            ).model_dump(mode="json"),
        )

    return APIResponse(success=True, data=result, error=None)


@router.get("/queue")
async def get_feasibility_queue(
    session: AsyncSession = Depends(get_db_session),
):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(
            success=False,
            data=None,
            error={"code": "NO_TENANT", "message": "No tenant context"},
        )
    rows = await session.execute(
        text("""
            SELECT
                mo.id, mo.feasibility_score, mo.primary_constraint,
                p.name AS product_name,
                dl.required_date,
                c.name AS customer_name,
                mo.erp_mo_id,
                mo.sync_conflict,
                (
                    SELECT COALESCE(json_agg(json_build_object(
                        'flag_code', f.flag_code,
                        'message', f.message
                    )), '[]'::json)
                    FROM cdm_data_quality_flag f
                    WHERE f.mo_id = mo.id AND f.tenant_id = mo.tenant_id
                      AND f.resolved_at IS NULL
                ) AS data_quality_flags
            FROM cdm_manufacturing_order mo
            LEFT JOIN cdm_demand_line dl ON dl.mo_id = mo.id
            LEFT JOIN cdm_product p ON p.id = mo.product_id
            LEFT JOIN cdm_customer c ON c.id = dl.customer_id
            WHERE mo.tenant_id = :tid
              AND (
                mo.feasibility_score IS NOT NULL
                OR EXISTS (
                    SELECT 1 FROM cdm_data_quality_flag f2
                    WHERE f2.mo_id = mo.id AND f2.tenant_id = mo.tenant_id
                      AND f2.resolved_at IS NULL
                )
              )
            ORDER BY mo.feasibility_score ASC NULLS FIRST
        """),
        {"tid": UUID(tenant_id)},
    )
    queue = []
    for r in rows.fetchall():
        flags = r[8] if r[8] else []
        sync_conflict = r[7]
        queue.append({
            "mo_id": str(r[0]),
            "feasibility_score": float(r[1]) if r[1] is not None else None,
            "primary_constraint": r[2],
            "product_name": r[3],
            "required_date": r[4].isoformat() if r[4] else None,
            "customer_name": r[5],
            "erp_mo_id": r[6],
            "sync_conflict": sync_conflict,
            "data_quality_flags": flags,
            "unscorable": r[1] is None and bool(flags),
        })
    return APIResponse(success=True, data=queue, error=None)


@router.get("/score/{mo_id}")
async def get_feasibility_score_by_mo(
    mo_id: UUID,
    session: AsyncSession = Depends(get_db_session),
):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})

    row = await session.execute(
        text("""
            SELECT feasibility_score, primary_constraint, material_score, capacity_score,
                   labor_score, status, autonomy_action
            FROM cdm_manufacturing_order
            WHERE id = :mo_id AND tenant_id = :tid
        """),
        {"mo_id": mo_id, "tid": UUID(tenant_id)},
    )
    mo = row.one_or_none()
    if not mo:
        return APIResponse(success=False, data=None, error={"code": "NOT_FOUND", "message": "MO not found"})

    data = {
        "mo_id": str(mo_id),
        "feasibility_score": float(mo[0]) if mo[0] is not None else None,
        "primary_constraint": mo[1],
        "material_score": float(mo[2]) if mo[2] is not None else None,
        "capacity_score": float(mo[3]) if mo[3] is not None else None,
        "labor_score": float(mo[4]) if mo[4] is not None else None,
        "status": mo[5],
        "action_taken": mo[6],
    }
    if mo[0] is not None:
        data["xai_explanation"] = XAIExplanation(
            constraints=[mo[1]] if mo[1] else [],
            assumptions=["db_backed_capacity_and_labor_scoring"],
            confidence_score=round(float(mo[0]) / 100.0, 4),
            contributing_factors={
                "material": round(float(mo[2] or 0) / 100.0 * 0.35, 4),
                "capacity": round(float(mo[3] or 0) / 100.0 * 0.30, 4),
                "labor": round(float(mo[4] or 0) / 100.0 * 0.25, 4),
            },
        ).model_dump()

    return APIResponse(success=True, data=data, error=None)


@router.post("/rescore/{mo_id}")
async def rescore_mo(
    mo_id: UUID,
    session: AsyncSession = Depends(get_db_session),
):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(
            success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"}
        )

    result = await score_from_mo(tenant_id=tenant_id, mo_id=str(mo_id), session=session)
    if "error" in result:
        return APIResponse(
            success=False, data=None, error={"code": "NOT_FOUND", "message": result["error"]}
        )

    result["xai_explanation"] = XAIExplanation(
        constraints=[result["primary_constraint"]] if result["primary_constraint"] != "none" else [],
        assumptions=["db_backed_capacity_and_labor_scoring"],
        confidence_score=round(result["feasibility_score"] / 100.0, 4),
        contributing_factors={
            "demand": round(result.get("gate_scores", {}).get("demand", 0) / 100.0 * 0.05, 4),
            "bom": round(result.get("gate_scores", {}).get("bom", 0) / 100.0 * 0.05, 4),
            "material": round(result.get("gate_scores", {}).get("material", 0) / 100.0 * 0.35, 4),
            "capacity": round(result.get("gate_scores", {}).get("capacity", 0) / 100.0 * 0.30, 4),
            "labor": round(result.get("gate_scores", {}).get("labor", 0) / 100.0 * 0.25, 4),
        },
    ).model_dump()

    return APIResponse(success=True, data=result, error=None)


@router.get("/kpis")
async def get_feasibility_kpis(
    session: AsyncSession = Depends(get_db_session),
):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(
            success=False,
            data=None,
            error={"code": "NO_TENANT", "message": "No tenant context"},
        )
    tid = UUID(tenant_id)

    avg_result = await session.execute(
        text(
            "SELECT AVG(feasibility_score) FROM cdm_manufacturing_order"
            " WHERE tenant_id = :tid AND feasibility_score IS NOT NULL"
        ),
        {"tid": tid},
    )
    avg_score = avg_result.scalar()
    avg_feasibility_score = round(float(avg_score), 1) if avg_score is not None else 0.0

    bottleneck_result = await session.execute(
        text("""
            SELECT COUNT(DISTINCT mo.id)
            FROM cdm_manufacturing_order mo
            WHERE mo.tenant_id = :tid
              AND mo.primary_constraint IS NOT NULL
              AND mo.feasibility_score IS NOT NULL
              AND mo.feasibility_score < 70
        """),
        {"tid": tid},
    )
    active_bottlenecks = bottleneck_result.scalar() or 0

    at_risk_result = await session.execute(
        text("""
            SELECT COUNT(*)
            FROM cdm_manufacturing_order
            WHERE tenant_id = :tid
              AND feasibility_score IS NOT NULL
              AND feasibility_score < 50
        """),
        {"tid": tid},
    )
    orders_at_risk = at_risk_result.scalar() or 0

    return APIResponse(
        success=True,
        data={
            "avg_feasibility_score": avg_feasibility_score,
            "active_bottlenecks": active_bottlenecks,
            "orders_at_risk": orders_at_risk,
            "otd_pct": None,
        },
        error=None,
    )


@router.get("/compliance-kpis")
async def compliance_kpis(
    session: AsyncSession = Depends(get_db_session),
    current_user: TokenPayload = Depends(require_roles(["planner", "admin", "manager", "auditor", "executive"])),
):
    """Compliance KPI dashboard data.

    Returns schedule adherence, AI decision audit counts, procurement accuracy,
    and energy/cost savings metrics.
    """
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})

    tid = UUID(tenant_id)

    # Schedule adherence: count of MOs with planned vs actual completion
    adherence_result = await session.execute(text("""
        SELECT
            COUNT(*) as total,
            COUNT(CASE WHEN planned_end <= actual_end THEN 1 END) as on_time,
            COUNT(CASE WHEN actual_end IS NOT NULL THEN 1 END) as completed
        FROM cdm_manufacturing_order
        WHERE tenant_id = :tid
    """), {"tid": tid})
    row = adherence_result.fetchone()
    total_mos = int(row[0] or 0) if row else 0
    on_time = int(row[1] or 0) if row else 0
    completed = int(row[2] or 0) if row else 0
    adherence_pct = round(on_time / max(1, completed) * 100, 1) if completed > 0 else None

    # AI decision audit: count of approvals vs rejections from audit log
    audit_result = await session.execute(text("""
        SELECT
            action,
            COUNT(*) as cnt
        FROM cdm_audit_log
        WHERE tenant_id = :tid
          AND action IN ('APPROVE_SCHEDULE', 'RUN_SCENARIO', 'COST_OPTIMIZE', 'COPILOT_CHAT')
        GROUP BY action
    """), {"tid": tid})
    audit_counts = {row[0]: int(row[1]) for row in audit_result.fetchall()}

    # AI decisions breakdown
    ai_decisions = {
        "approvals": audit_counts.get("APPROVE_SCHEDULE", 0),
        "scenario_runs": audit_counts.get("RUN_SCENARIO", 0),
        "cost_optimizations": audit_counts.get("COST_OPTIMIZE", 0),
        "copilot_interactions": audit_counts.get("COPILOT_CHAT", 0),
        "total_ai_decisions": sum(audit_counts.values()),
    }

    # Energy/cost savings from cost-optimized schedules
    cost_result = await session.execute(text("""
        SELECT
            COUNT(*) as total_schedules,
            AVG((after_state->>'total_cost')::float) as avg_total_cost
        FROM cdm_audit_log
        WHERE tenant_id = :tid
          AND action = 'COST_OPTIMIZE'
          AND after_state IS NOT NULL
    """), {"tid": tid})
    cost_row = cost_result.fetchone()
    total_schedules = int(cost_row[0] or 0) if cost_row else 0
    avg_cost = float(cost_row[1] or 0) if cost_row else 0

    # Recent audit log entries
    recent_result = await session.execute(text("""
        SELECT
            timestamp, actor_id, action, entity_type, entity_id, rationale
        FROM cdm_audit_log
        WHERE tenant_id = :tid
        ORDER BY timestamp DESC
        LIMIT 20
    """), {"tid": tid})
    recent_audit = [
        {
            "timestamp": str(r[0]),
            "actor_id": r[1],
            "action": r[2],
            "entity_type": r[3],
            "entity_id": str(r[4]),
            "rationale": r[5],
        }
        for r in recent_result.fetchall()
    ]

    return APIResponse(
        success=True,
        data={
            "schedule_adherence": {
                "total_mos": total_mos,
                "completed": completed,
                "on_time": on_time,
                "adherence_pct": adherence_pct,
            },
            "ai_decisions": ai_decisions,
            "cost_savings": {
                "total_schedules_optimized": total_schedules,
                "avg_total_cost": round(avg_cost, 2),
            },
            "recent_audit_log": recent_audit,
        },
        error=None,
    )
