"""Compliance evidence API endpoints for SOC 2 / ISO 27001."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from ipe_shared.compliance.evidence import generate_evidence_report, ComplianceEvidenceReport
from ipe_shared.database.session import get_session

router = APIRouter(prefix="/compliance", tags=["compliance"])


@router.get("/soc2/evidence", response_model=ComplianceEvidenceReport)
async def get_soc2_evidence(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> ComplianceEvidenceReport:
    """Generate SOC 2 compliance evidence report across all 5 trust principles."""
    report = await generate_evidence_report(session)
    return report


@router.get("/soc2/summary")
async def get_soc2_summary(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Quick SOC 2 summary — control counts and coverage."""
    report = await generate_evidence_report(session)
    return {
        "total_controls": report.total_controls,
        "implemented": report.implemented,
        "coverage_pct": report.coverage_pct,
        "principles": report.principles,
    }
