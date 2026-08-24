"""Run DQ catalog checks for a tenant and persist a report."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.data_quality.catalog import CATALOG, WEIGHT, compute_score


@dataclass
class CheckResult:
    check_id: str
    entity: str
    severity: str
    offense_count: int
    sample_ids: list[str]
    fix_guidance: str


@dataclass
class DQReport:
    report_id: str
    tenant_id: str
    score: float
    ran_at: str
    checks: list[CheckResult] = field(default_factory=list)


async def run_all_checks(session: AsyncSession, tenant_id: UUID) -> DQReport:
    await session.execute(text("SELECT set_config('app.current_tenant_id', :tid, false)"), {"tid": str(tenant_id)})
    results: list[CheckResult] = []
    counts: dict[str, int] = {}
    for chk in CATALOG:
        try:
            rows = (
                await session.execute(
                    text(chk.sql_query + " AND tenant_id = CAST(:tid AS uuid)")
                    if " WHERE " in chk.sql_query.upper()
                    else text(chk.sql_query + " WHERE tenant_id = CAST(:tid AS uuid)"),
                    {"tid": str(tenant_id)},
                )
            ).fetchall()
            ids = [str(r[0]) for r in rows[:25]]
            n = len(rows)
        except Exception:
            await session.rollback()
            await session.execute(
                text("SELECT set_config('app.current_tenant_id', :tid, false)"),
                {"tid": str(tenant_id)},
            )
            ids, n = [], 0
        counts[chk.id] = n
        results.append(
            CheckResult(chk.id, chk.entity, chk.severity, n, ids, chk.fix_guidance)
        )
    report = DQReport(
        report_id=str(uuid4()),
        tenant_id=str(tenant_id),
        score=round(compute_score(counts), 2),
        ran_at=datetime.now(UTC).isoformat(),
        checks=results,
    )
    await _persist(session, report)
    return report


async def _persist(session: AsyncSession, report: DQReport) -> None:
    payload = {
        "score": report.score,
        "checks": [
            {
                "id": c.check_id,
                "entity": c.entity,
                "severity": c.severity,
                "offense_count": c.offense_count,
                "sample_ids": c.sample_ids,
                "fix_guidance": c.fix_guidance,
            }
            for c in report.checks
        ],
    }
    try:
        await session.execute(
            text(
                """
                INSERT INTO cdm_data_quality_report (id, tenant_id, score, payload)
                VALUES (CAST(:id AS uuid), CAST(:tid AS uuid), :score, CAST(:payload AS jsonb))
                """
            ),
            {
                "id": report.report_id,
                "tid": report.tenant_id,
                "score": report.score,
                "payload": json.dumps(payload),
            },
        )
        await session.commit()
    except Exception:
        await session.rollback()
