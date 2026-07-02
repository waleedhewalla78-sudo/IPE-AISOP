"""Master Data Readiness (MDR) composite score engine."""

from __future__ import annotations

import logging
import os
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ipe_shared.database.session import tenant_ctx

logger = logging.getLogger(__name__)

BOM_COMPLETENESS_THRESHOLD = float(os.getenv("MDR_BOM_THRESHOLD", "80"))
LEAD_TIME_ACCURACY_THRESHOLD = float(os.getenv("MDR_LEAD_TIME_THRESHOLD", "60"))
COMPOSITE_THRESHOLD = float(os.getenv("MDR_QUALITY_GATE_THRESHOLD", "70"))

ROUTING_DEVIATION_THRESHOLD_PCT = float(os.getenv("MDR_ROUTING_DEVIATION_THRESHOLD", "15"))


async def calculate_mdr(session: AsyncSession, tenant_id: str | None = None) -> dict:
    tid = tenant_id or tenant_ctx.get()
    if not tid:
        return {
            "bom_completeness_pct": 0.0,
            "lead_time_accuracy_pct": 0.0,
            "passed": False,
            "error": "No tenant context",
        }

    await session.execute(
        text("SELECT set_config('app.current_tenant_id', :tid, false)"),
        {"tid": tid},
    )

    bom_result = await session.execute(
        text("""
            SELECT
                COUNT(DISTINCT p.id) AS total_manufactured,
                COUNT(DISTINCT b.product_id) AS with_bom
            FROM cdm_product p
            LEFT JOIN cdm_bill_of_material b
                ON b.product_id = p.id AND b.is_active = true
            WHERE p.source_type = 'manufactured'
              AND p.tenant_id = :tid
        """),
        {"tid": UUID(tid)},
    )
    bom_row = bom_result.fetchone()
    total_manufactured = max(float(bom_row[0]), 1)
    with_bom = float(bom_row[1])
    bom_completeness_pct = round((with_bom / total_manufactured) * 100, 2)

    lt_result = await session.execute(
        text("""
            SELECT
                COUNT(*) AS total_products,
                COUNT(*) FILTER (WHERE lead_time_days IS NOT NULL) AS with_lead_time
            FROM cdm_product
            WHERE tenant_id = :tid
        """),
        {"tid": UUID(tid)},
    )
    lt_row = lt_result.fetchone()
    total_products = max(float(lt_row[0]), 1)
    with_lead_time = float(lt_row[1])
    lead_time_accuracy_pct = round((with_lead_time / total_products) * 100, 2)

    routing_result = await session.execute(
        text("""
            SELECT
                COUNT(*) AS total_mos,
                COUNT(*) FILTER (
                    WHERE mo.bom_id IS NOT NULL
                      AND EXISTS (
                        SELECT 1 FROM cdm_routing_operation r
                        WHERE r.bom_id = mo.bom_id AND r.tenant_id = mo.tenant_id
                    )
                ) AS with_routing
            FROM cdm_manufacturing_order mo
            WHERE mo.tenant_id = :tid
        """),
        {"tid": UUID(tid)},
    )
    routing_row = routing_result.fetchone()
    total_mos = max(float(routing_row[0]), 1)
    with_routing = float(routing_row[1])
    routing_accuracy_pct = round((with_routing / total_mos) * 100, 2)

    inv_result = await session.execute(
        text("""
            SELECT
                COUNT(DISTINCT p.id) AS total_products,
                COUNT(DISTINCT ip.product_id) AS with_inventory
            FROM cdm_product p
            LEFT JOIN cdm_inventory_position ip
                ON ip.product_id = p.id AND ip.tenant_id = p.tenant_id
            WHERE p.tenant_id = :tid
        """),
        {"tid": UUID(tid)},
    )
    inv_row = inv_result.fetchone()
    total_inv_products = max(float(inv_row[0]), 1)
    with_inventory = float(inv_row[1])
    inventory_accuracy_pct = round((with_inventory / total_inv_products) * 100, 2)

    composite_score = round(
        bom_completeness_pct * 0.40
        + routing_accuracy_pct * 0.35
        + inventory_accuracy_pct * 0.25,
        2,
    )

    passed = (
        bom_completeness_pct >= BOM_COMPLETENESS_THRESHOLD
        and lead_time_accuracy_pct >= LEAD_TIME_ACCURACY_THRESHOLD
    )
    ai_scheduling_allowed = composite_score >= COMPOSITE_THRESHOLD

    await session.execute(
        text("""
            INSERT INTO cdm_mdr_score (tenant_id, bom_completeness_pct, lead_time_accuracy_pct, passed)
            VALUES (:tid, :bom_pct, :lt_pct, :passed)
        """),
        {
            "tid": UUID(tid),
            "bom_pct": bom_completeness_pct,
            "lt_pct": lead_time_accuracy_pct,
            "passed": passed,
        },
    )
    await session.commit()

    payload = {
        "bom_completeness_pct": bom_completeness_pct,
        "lead_time_accuracy_pct": lead_time_accuracy_pct,
        "routing_accuracy_pct": routing_accuracy_pct,
        "inventory_accuracy_pct": inventory_accuracy_pct,
        "composite_score": composite_score,
        "composite_threshold": COMPOSITE_THRESHOLD,
        "overall_score": composite_score,
        "readiness_score": composite_score,
        "ai_scheduling_allowed": ai_scheduling_allowed,
        "passed": passed,
        "remediation": build_remediation({
            "bom_completeness_pct": bom_completeness_pct,
            "lead_time_accuracy_pct": lead_time_accuracy_pct,
            "routing_accuracy_pct": routing_accuracy_pct,
            "inventory_accuracy_pct": inventory_accuracy_pct,
            "composite_score": composite_score,
        }),
    }
    return payload


def build_remediation(mdr: dict) -> list[str]:
    steps = []
    if mdr.get("composite_score", 100) < COMPOSITE_THRESHOLD:
        steps.append(
            f"Composite MDR score {mdr.get('composite_score', 0):.1f}% "
            f"(need ≥ {COMPOSITE_THRESHOLD:.0f}%) — fix dimensions below"
        )
    if mdr["bom_completeness_pct"] < BOM_COMPLETENESS_THRESHOLD:
        steps.append(
            f"Update BOMs: {mdr['bom_completeness_pct']:.1f}% completeness "
            f"(need ≥ {BOM_COMPLETENESS_THRESHOLD:.0f}%)"
        )
    if mdr["lead_time_accuracy_pct"] < LEAD_TIME_ACCURACY_THRESHOLD:
        steps.append(
            f"Verify vendor lead times: {mdr['lead_time_accuracy_pct']:.1f}% accuracy "
            f"(need ≥ {LEAD_TIME_ACCURACY_THRESHOLD:.0f}%)"
        )
    if mdr.get("routing_accuracy_pct", 100) < 80:
        steps.append(
            f"Add routing operations: {mdr.get('routing_accuracy_pct', 0):.1f}% MO coverage"
        )
    if mdr.get("inventory_accuracy_pct", 100) < 70:
        steps.append(
            f"Reconcile inventory records: {mdr.get('inventory_accuracy_pct', 0):.1f}% product coverage"
        )
    return steps


def format_mdr_response(tenant_id: str, mdr: dict) -> dict:
    """Public API shape for feasibility/mdr dashboard."""
    return {
        "tenant_id": tenant_id,
        "composite_score": mdr.get("composite_score", 0.0),
        "threshold": mdr.get("composite_threshold", COMPOSITE_THRESHOLD),
        "passing": mdr.get("ai_scheduling_allowed", False),
        "dimensions": {
            "bom_coverage": mdr.get("bom_completeness_pct", 0.0),
            "routing_coverage": mdr.get("routing_accuracy_pct", 0.0),
            "inventory_coverage": mdr.get("inventory_accuracy_pct", 0.0),
            "lead_time_coverage": mdr.get("lead_time_accuracy_pct", 0.0),
        },
        "recommendations": mdr.get("remediation", []),
        "formula": "composite = 0.40×BOM + 0.35×routing + 0.25×inventory",
    }


async def detect_routing_deviation(
    session: AsyncSession,
    tenant_id: str | None = None,
    *,
    threshold_pct: float = ROUTING_DEVIATION_THRESHOLD_PCT,
) -> list[dict]:
    tid = tenant_id or tenant_ctx.get()
    if not tid:
        return []

    await session.execute(
        text("SELECT set_config('app.current_tenant_id', :tid, false)"),
        {"tid": tid},
    )

    result = await session.execute(
        text("""
            SELECT
                r.id AS routing_id,
                r.id AS operation_id,
                r.duration_planned_mins AS standard_before,
                COALESCE(r.duration_predicted_mins, wo.duration_actual_mins, r.duration_planned_mins) AS observed,
                wo.mo_id
            FROM cdm_routing_operation r
            LEFT JOIN cdm_work_order wo
                ON wo.routing_op_id = r.id AND wo.tenant_id = r.tenant_id
            WHERE r.tenant_id = :tid
              AND r.duration_planned_mins > 0
        """),
        {"tid": UUID(tid)},
    )
    rows = result.fetchall()
    drafts: list[dict] = []

    for row in rows:
        standard_before = float(row[2] or 0)
        observed = float(row[3] or standard_before)
        if standard_before <= 0:
            continue
        deviation_pct = abs(observed - standard_before) / standard_before * 100.0
        if deviation_pct < threshold_pct:
            continue
        standard_after = round(observed, 2)
        drafts.append({
            "routing_id": str(row[0]),
            "operation_id": str(row[1]),
            "standard_time_before_mins": round(standard_before, 2),
            "standard_time_after_mins": standard_after,
            "deviation_pct": round(deviation_pct, 2),
            "status": "pending_approval",
            "mo_id": str(row[4]) if row[4] else None,
        })

    return drafts
