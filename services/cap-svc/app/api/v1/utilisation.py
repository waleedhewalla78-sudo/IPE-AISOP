from __future__ import annotations

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select as sa_select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.utilisation import DEFAULT_OVERLOAD_THRESHOLD_PCT, UtilisationCalculator
from ipe_shared.auth.jwt import TokenPayload
from ipe_shared.auth.rbac import require_roles
from ipe_shared.database.session import get_session as get_db_session
from ipe_shared.middleware.tenant_context import tenant_ctx
from ipe_shared.models.planning_intelligence import CapacityAlertConfig, CapacityUtilisation
from ipe_shared.schemas.common import APIResponse

router = APIRouter(prefix="/capacity/utilisation", tags=["capacity-utilisation"])


class CalculateUtilisationRequest(BaseModel):
    period_start: date | None = None
    period_type: str = "week"


class CapacityAlertConfigRequest(BaseModel):
    overload_threshold_pct: float = Field(default=90.0, ge=0)
    critical_threshold_pct: float = Field(default=100.0, ge=0)
    alert_enabled: bool = True


def _tenant_uuid() -> UUID | None:
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return None
    return UUID(str(tenant_id))


def _no_tenant() -> APIResponse:
    return APIResponse(
        success=False,
        data=None,
        error={"code": "NO_TENANT", "message": "No tenant context"},
    )


def _row_to_dict(row: CapacityUtilisation) -> dict:
    return {
        "id": str(row.id) if row.id else None,
        "work_center_id": str(row.work_center_id),
        "period_start": row.period_start.isoformat() if row.period_start else None,
        "period_type": row.period_type,
        "capacity_available_hours": float(row.capacity_available_hours or 0),
        "capacity_used_hours": float(row.capacity_used_hours or 0),
        "utilisation_pct": float(row.utilisation_pct or 0),
        "overload": bool(row.overload),
        "overload_hours": float(row.overload_hours or 0),
        "calculated_at": row.calculated_at.isoformat() if row.calculated_at else None,
    }


def _config_to_dict(config: CapacityAlertConfig | None) -> dict:
    return {
        "overload_threshold_pct": float(
            config.overload_threshold_pct if config else DEFAULT_OVERLOAD_THRESHOLD_PCT
        ),
        "critical_threshold_pct": float(config.critical_threshold_pct if config else 100.0),
        "alert_enabled": bool(config.alert_enabled) if config else True,
    }


async def _get_config(session: AsyncSession, tenant_id: UUID) -> CapacityAlertConfig | None:
    return (
        await session.execute(
            sa_select(CapacityAlertConfig).where(CapacityAlertConfig.tenant_id == tenant_id)
        )
    ).scalar_one_or_none()


async def _list_rows(session: AsyncSession, tenant_id: UUID) -> list[CapacityUtilisation]:
    return (
        await session.execute(
            sa_select(CapacityUtilisation)
            .where(CapacityUtilisation.tenant_id == tenant_id)
            .order_by(CapacityUtilisation.period_start.desc(), CapacityUtilisation.utilisation_pct.desc())
        )
    ).scalars().all()


@router.post("/calculate")
async def calculate_utilisation(
    req: CalculateUtilisationRequest | None = None,
    session: AsyncSession = Depends(get_db_session),
    _user: TokenPayload = Depends(require_roles(["planner", "admin", "manager", "supervisor"])),
):
    tenant_id = _tenant_uuid()
    if tenant_id is None:
        return _no_tenant()

    payload = req or CalculateUtilisationRequest()
    rows = await UtilisationCalculator().calculate(
        session,
        tenant_id,
        period_start=payload.period_start,
        period_type=payload.period_type,
    )
    return APIResponse(success=True, data={"rows": [_row_to_dict(row) for row in rows]}, error=None)


@router.get("/")
async def list_utilisation(
    session: AsyncSession = Depends(get_db_session),
    _user: TokenPayload = Depends(require_roles(["planner", "admin", "manager", "supervisor", "executive"])),
):
    tenant_id = _tenant_uuid()
    if tenant_id is None:
        return _no_tenant()

    rows = await _list_rows(session, tenant_id)
    return APIResponse(success=True, data={"rows": [_row_to_dict(row) for row in rows]}, error=None)


@router.get("/alerts")
async def utilisation_alerts(
    session: AsyncSession = Depends(get_db_session),
    _user: TokenPayload = Depends(require_roles(["planner", "admin", "manager", "supervisor", "executive"])),
):
    tenant_id = _tenant_uuid()
    if tenant_id is None:
        return _no_tenant()

    config = await _get_config(session, tenant_id)
    cfg = _config_to_dict(config)
    rows = await _list_rows(session, tenant_id)
    alerts = [
        {
            **_row_to_dict(row),
            "severity": "critical"
            if float(row.utilisation_pct or 0) >= cfg["critical_threshold_pct"]
            else "warning",
        }
        for row in rows
        if cfg["alert_enabled"] and float(row.utilisation_pct or 0) >= cfg["overload_threshold_pct"]
    ]
    return APIResponse(success=True, data={"alerts": alerts, "config": cfg}, error=None)


@router.get("/ranking")
async def utilisation_ranking(
    session: AsyncSession = Depends(get_db_session),
    _user: TokenPayload = Depends(require_roles(["planner", "admin", "manager", "supervisor", "executive"])),
):
    tenant_id = _tenant_uuid()
    if tenant_id is None:
        return _no_tenant()

    rows = await _list_rows(session, tenant_id)
    ranking = sorted(
        [_row_to_dict(row) for row in rows],
        key=lambda row: row["utilisation_pct"],
        reverse=True,
    )
    return APIResponse(success=True, data={"ranking": ranking}, error=None)


@router.get("/config")
async def get_utilisation_config(
    session: AsyncSession = Depends(get_db_session),
    _user: TokenPayload = Depends(require_roles(["planner", "admin", "manager", "supervisor"])),
):
    tenant_id = _tenant_uuid()
    if tenant_id is None:
        return _no_tenant()

    config = await _get_config(session, tenant_id)
    return APIResponse(success=True, data=_config_to_dict(config), error=None)


@router.put("/config")
async def update_utilisation_config(
    req: CapacityAlertConfigRequest,
    session: AsyncSession = Depends(get_db_session),
    _user: TokenPayload = Depends(require_roles(["planner", "admin", "manager"])),
):
    tenant_id = _tenant_uuid()
    if tenant_id is None:
        return _no_tenant()

    config = await _get_config(session, tenant_id)
    if config is None:
        config = CapacityAlertConfig(tenant_id=tenant_id)
        session.add(config)

    config.overload_threshold_pct = req.overload_threshold_pct
    config.critical_threshold_pct = req.critical_threshold_pct
    config.alert_enabled = req.alert_enabled
    await session.commit()
    return APIResponse(success=True, data=_config_to_dict(config), error=None)
