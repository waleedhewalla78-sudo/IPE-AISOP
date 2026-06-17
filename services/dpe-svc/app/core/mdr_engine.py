import logging
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ipe_shared.database.session import tenant_ctx

logger = logging.getLogger(__name__)

BOM_COMPLETENESS_THRESHOLD = 80.0
LEAD_TIME_ACCURACY_THRESHOLD = 60.0


async def calculate_mdr(session: AsyncSession, tenant_id: str | None = None) -> dict:
    tid = tenant_id or tenant_ctx.get()
    if not tid:
        return {
            "bom_completeness_pct": 0.0,
            "lead_time_accuracy_pct": 0.0,
            "passed": False,
            "error": "No tenant context",
        }

    # Set tenant context for RLS
    await session.execute(
        text("SELECT set_config('app.current_tenant_id', :tid, false)"),
        {"tid": tid},
    )

    # BOM completeness: manufactured products WITH active BOM / total manufactured products
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

    # Lead time accuracy: products WITH non-null lead_time_days / total products
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

    passed = (
        bom_completeness_pct >= BOM_COMPLETENESS_THRESHOLD
        and lead_time_accuracy_pct >= LEAD_TIME_ACCURACY_THRESHOLD
    )

    # Persist to cdm_mdr_score
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

    return {
        "bom_completeness_pct": bom_completeness_pct,
        "lead_time_accuracy_pct": lead_time_accuracy_pct,
        "passed": passed,
    }


def build_remediation(mdr: dict) -> list[str]:
    steps = []
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
    return steps
