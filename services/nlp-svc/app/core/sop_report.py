"""S&OP synthesis report builder (Sprint S11)."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

import httpx
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ipe_shared.models.manufacturing_order import ManufacturingOrder
from ipe_shared.models.sop_forecast import SopForecast
from ipe_shared.models.sop_report import SopReport


async def _fetch_sop_gap(dpe_url: str, tenant_id: str) -> dict:
    """Call dpe-svc S&OP solve with empty payload fallback."""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"{dpe_url}/api/v1/sop/solve",
                json={"demand": [], "capacity": [], "bottleneck_threshold_pct": 10.0},
                headers={"X-Tenant-ID": tenant_id},
            )
            if resp.status_code == 200:
                return resp.json().get("data") or {}
    except Exception:
        pass
    return {"bottlenecks": [], "gap_summary": {}}


async def build_sop_report(
    session: AsyncSession,
    tenant_id: UUID,
    dpe_url: str,
    report_name: str,
    horizon_weeks: int,
    generated_by: str | None = None,
) -> SopReport:
    forecast_count = (
        await session.execute(
            select(func.count()).where(SopForecast.tenant_id == tenant_id)
        )
    ).scalar() or 0

    active_mos = (
        await session.execute(
            select(func.count()).where(
                ManufacturingOrder.tenant_id == tenant_id,
                ManufacturingOrder.status.in_(["planned", "in_progress", "released"]),
            )
        )
    ).scalar() or 0

    gap_data = await _fetch_sop_gap(dpe_url, str(tenant_id))
    bottlenecks = gap_data.get("bottlenecks") or gap_data.get("gap_analysis", {}).get("bottlenecks") or []

    recommendations = []
    if bottlenecks:
        recommendations.append(
            {
                "priority": "high",
                "action": "Increase capacity or defer demand in bottleneck periods",
                "bottleneck_count": len(bottlenecks),
            }
        )
    if active_mos > 50:
        recommendations.append(
            {
                "priority": "medium",
                "action": "Review WIP levels — active MO count exceeds planning threshold",
                "active_mo_count": int(active_mos),
            }
        )
    if forecast_count == 0:
        recommendations.append(
            {
                "priority": "medium",
                "action": "Ingest S&OP forecast data for the planning horizon",
            }
        )

    summary = {
        "horizon_weeks": horizon_weeks,
        "forecast_buckets": int(forecast_count),
        "active_mo_count": int(active_mos),
        "bottleneck_count": len(bottlenecks),
        "generated_at": datetime.now(UTC).isoformat(),
    }

    report = SopReport(
        tenant_id=tenant_id,
        report_name=report_name,
        horizon_weeks=horizon_weeks,
        status="published",
        summary=summary,
        gap_analysis={"bottlenecks": bottlenecks, "raw": gap_data},
        recommendations=recommendations,
        generated_by=generated_by,
    )
    session.add(report)
    await session.flush()
    return report


def report_to_dict(report: SopReport) -> dict:
    return {
        "report_id": str(report.id),
        "report_name": report.report_name,
        "horizon_weeks": report.horizon_weeks,
        "status": report.status,
        "summary": report.summary,
        "gap_analysis": report.gap_analysis,
        "recommendations": report.recommendations,
        "generated_by": report.generated_by,
        "generated_at": report.generated_at.isoformat() if report.generated_at else None,
    }
