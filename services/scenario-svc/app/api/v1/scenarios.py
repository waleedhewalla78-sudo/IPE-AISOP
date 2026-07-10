from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.simulator import DEFAULT_BASELINE, compare_scenarios, simulate_kpis
from ipe_shared.auth.jwt import TokenPayload
from ipe_shared.auth.rbac import require_roles
from ipe_shared.database.session import get_session as get_db_session
from ipe_shared.middleware.tenant_context import tenant_ctx
from ipe_shared.models.v8_planning import PlanningScenario, ScenarioParameter, ScenarioResult
from ipe_shared.schemas.common import APIResponse

router = APIRouter(prefix="/scenario", tags=["scenario"])


class CreateScenarioRequest(BaseModel):
    name: str = Field(min_length=3, max_length=128)
    description: str | None = None
    clone_from_id: UUID | None = None


class ParameterUpdate(BaseModel):
    parameter_key: str
    parameter_value: str
    data_type: str = "string"
    description: str | None = None


class ParameterBatchRequest(BaseModel):
    parameters: list[ParameterUpdate]


DEFAULT_PARAMS = [
    ParameterUpdate(parameter_key="demand_change_pct", parameter_value="0%", description="Demand delta"),
    ParameterUpdate(
        parameter_key="supplier_delay_days",
        parameter_value="0",
        data_type="integer",
        description="Supplier lead-time delay (days)",
    ),
    ParameterUpdate(
        parameter_key="capacity_reduction_pct",
        parameter_value="0%",
        description="Capacity reduction",
    ),
]


class SimulateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=3, max_length=128)
    description: str | None = None
    demand_change_pct: str = "0%"
    supplier_delay_days: str = "0"
    capacity_reduction_pct: str = "0%"
    persist: bool = True


async def _params_map(session: AsyncSession, scenario_id: UUID) -> dict[str, str]:
    result = await session.execute(
        select(ScenarioParameter).where(ScenarioParameter.scenario_id == scenario_id)
    )
    return {row.parameter_key: row.parameter_value for row in result.scalars().all()}


def _params_from_simulate(req: SimulateRequest) -> dict[str, str]:
    return {
        "demand_change_pct": req.demand_change_pct,
        "supplier_delay_days": req.supplier_delay_days,
        "capacity_reduction_pct": req.capacity_reduction_pct,
    }


@router.post("/simulate")
async def simulate_ad_hoc(
    req: SimulateRequest,
    session: AsyncSession = Depends(get_db_session),
    user: TokenPayload = Depends(require_roles(["planner", "admin", "manager"])),
):
    """Run what-if simulation; optionally persist as a scenario (max 3 active per tenant)."""
    tenant_id = tenant_ctx.get()
    params = _params_from_simulate(req)
    kpis = simulate_kpis(params)
    baseline = dict(DEFAULT_BASELINE)
    deltas = {k: round(kpis.get(k, 0) - baseline.get(k, 0), 2) for k in baseline}

    if not req.persist:
        return APIResponse(
            success=True,
            data={"baseline": baseline, "kpis": kpis, "deltas": deltas, "parameters": params},
            error=None,
        )

    active_count = (
        await session.execute(
            select(PlanningScenario).where(
                PlanningScenario.tenant_id == tenant_id,
                PlanningScenario.status == "active",
            )
        )
    ).scalars().all()
    if len(active_count) >= 3:
        return APIResponse(
            success=False,
            data=None,
            error={"code": "LIMIT", "message": "Maximum 3 active scenarios; archive one before saving"},
        )

    scenario_name = req.name or f"What-if {datetime.now(UTC).strftime('%Y-%m-%d %H:%M')}"
    scenario = PlanningScenario(
        tenant_id=tenant_id,
        name=scenario_name,
        description=req.description,
        status="active",
        created_by=str(user.sub),
    )
    session.add(scenario)
    await session.flush()

    for key, value in params.items():
        session.add(
            ScenarioParameter(
                tenant_id=tenant_id,
                scenario_id=scenario.id,
                parameter_key=key,
                parameter_value=value,
                data_type="integer" if key.endswith("_days") else "string",
            )
        )
    for key, value in kpis.items():
        session.add(
            ScenarioResult(
                tenant_id=tenant_id,
                scenario_id=scenario.id,
                kpi_key=key,
                kpi_value=value,
                unit="pct" if key.endswith("_pct") else "usd" if key.endswith("_usd") else "count",
            )
        )
    scenario.completed_at = datetime.now(UTC)
    await session.commit()
    return APIResponse(
        success=True,
        data={
            "scenario_id": str(scenario.id),
            "name": scenario.name,
            "baseline": baseline,
            "kpis": kpis,
            "deltas": deltas,
            "parameters": params,
        },
        error=None,
    )


@router.post("")
async def create_scenario(
    req: CreateScenarioRequest,
    session: AsyncSession = Depends(get_db_session),
    user: TokenPayload = Depends(require_roles(["planner", "admin", "manager"])),
):
    tenant_id = tenant_ctx.get()
    scenario = PlanningScenario(
        tenant_id=tenant_id,
        name=req.name,
        description=req.description,
        base_scenario_id=req.clone_from_id,
        status="active",
        created_by=str(user.sub),
    )
    session.add(scenario)
    await session.flush()

    seed = DEFAULT_PARAMS
    if req.clone_from_id:
        seed = [
            ParameterUpdate(
                parameter_key=p.parameter_key,
                parameter_value=p.parameter_value,
                data_type=p.data_type,
                description=p.description,
            )
            for p in (
                await session.execute(
                    select(ScenarioParameter).where(ScenarioParameter.scenario_id == req.clone_from_id)
                )
            ).scalars().all()
        ] or DEFAULT_PARAMS

    for param in seed:
        session.add(
            ScenarioParameter(
                tenant_id=tenant_id,
                scenario_id=scenario.id,
                parameter_key=param.parameter_key,
                parameter_value=param.parameter_value,
                data_type=param.data_type,
                description=param.description,
            )
        )
    await session.commit()
    return APIResponse(success=True, data={"scenario_id": str(scenario.id), "name": scenario.name}, error=None)


@router.get("/compare")
async def compare(
    ids: str = Query(..., description="Comma-separated scenario UUIDs"),
    session: AsyncSession = Depends(get_db_session),
    _user=Depends(require_roles(["planner", "admin", "manager", "executive"])),
):
    tenant_id = tenant_ctx.get()
    scenario_ids = [UUID(s.strip()) for s in ids.split(",") if s.strip()]
    all_results: list[dict[str, float]] = []
    meta = []
    for sid in scenario_ids:
        scenario = await session.get(PlanningScenario, sid)
        if not scenario or str(scenario.tenant_id) != tenant_id:
            continue
        rows = (
            await session.execute(select(ScenarioResult).where(ScenarioResult.scenario_id == sid))
        ).scalars().all()
        kpi_map = {r.kpi_key: float(r.kpi_value) for r in rows}
        all_results.append(kpi_map)
        meta.append({"id": str(sid), "name": scenario.name, "kpis": kpi_map})

    comparison = compare_scenarios(all_results, DEFAULT_BASELINE)
    for i, item in enumerate(comparison):
        if i < len(meta):
            item["scenario"] = meta[i]
    return APIResponse(
        success=True,
        data={"baseline": DEFAULT_BASELINE, "comparisons": comparison},
        error=None,
    )


@router.get("")
async def list_scenarios(
    session: AsyncSession = Depends(get_db_session),
    _user=Depends(require_roles(["planner", "admin", "manager", "executive"])),
):
    tenant_id = tenant_ctx.get()
    rows = (
        await session.execute(
            select(PlanningScenario)
            .where(
                PlanningScenario.tenant_id == tenant_id,
                PlanningScenario.status != "archived",
            )
            .order_by(PlanningScenario.created_at.desc())
            .limit(50)
        )
    ).scalars().all()
    return APIResponse(
        success=True,
        data={
            "scenarios": [
                {
                    "id": str(s.id),
                    "name": s.name,
                    "description": s.description,
                    "status": s.status,
                    "created_at": s.created_at.isoformat() if s.created_at else None,
                }
                for s in rows
            ]
        },
        error=None,
    )


@router.get("/{scenario_id}")
async def get_scenario(
    scenario_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    _user=Depends(require_roles(["planner", "admin", "manager", "executive"])),
):
    tenant_id = tenant_ctx.get()
    scenario = await session.get(PlanningScenario, scenario_id)
    if not scenario or str(scenario.tenant_id) != tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NOT_FOUND", "message": "Scenario not found"})
    params = await _params_map(session, scenario_id)
    results = (
        await session.execute(select(ScenarioResult).where(ScenarioResult.scenario_id == scenario_id))
    ).scalars().all()
    return APIResponse(
        success=True,
        data={
            "id": str(scenario.id),
            "name": scenario.name,
            "description": scenario.description,
            "status": scenario.status,
            "parameters": params,
            "results": [
                {"kpi_key": r.kpi_key, "kpi_value": float(r.kpi_value), "unit": r.unit}
                for r in results
            ],
        },
        error=None,
    )


@router.put("/{scenario_id}/parameters")
async def update_parameters(
    scenario_id: UUID,
    req: ParameterBatchRequest,
    session: AsyncSession = Depends(get_db_session),
    _user=Depends(require_roles(["planner", "admin", "manager"])),
):
    tenant_id = tenant_ctx.get()
    scenario = await session.get(PlanningScenario, scenario_id)
    if not scenario or str(scenario.tenant_id) != tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NOT_FOUND", "message": "Scenario not found"})

    for param in req.parameters:
        existing = (
            await session.execute(
                select(ScenarioParameter).where(
                    ScenarioParameter.scenario_id == scenario_id,
                    ScenarioParameter.parameter_key == param.parameter_key,
                )
            )
        ).scalar_one_or_none()
        if existing:
            existing.parameter_value = param.parameter_value
            existing.data_type = param.data_type
            existing.description = param.description
        else:
            session.add(
                ScenarioParameter(
                    tenant_id=tenant_id,
                    scenario_id=scenario_id,
                    parameter_key=param.parameter_key,
                    parameter_value=param.parameter_value,
                    data_type=param.data_type,
                    description=param.description,
                )
            )
    await session.commit()
    return APIResponse(success=True, data={"updated": len(req.parameters)}, error=None)


@router.post("/{scenario_id}/simulate")
async def simulate_scenario(
    scenario_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    _user=Depends(require_roles(["planner", "admin", "manager"])),
):
    tenant_id = tenant_ctx.get()
    scenario = await session.get(PlanningScenario, scenario_id)
    if not scenario or str(scenario.tenant_id) != tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NOT_FOUND", "message": "Scenario not found"})

    params = await _params_map(session, scenario_id)
    kpis = simulate_kpis(params)
    await session.execute(delete(ScenarioResult).where(ScenarioResult.scenario_id == scenario_id))
    for key, value in kpis.items():
        session.add(
            ScenarioResult(
                tenant_id=tenant_id,
                scenario_id=scenario_id,
                kpi_key=key,
                kpi_value=value,
                unit="pct" if key.endswith("_pct") else "usd" if key.endswith("_usd") else "count",
            )
        )
    scenario.completed_at = datetime.now(UTC)
    await session.commit()
    return APIResponse(success=True, data={"scenario_id": str(scenario_id), "kpis": kpis}, error=None)


@router.post("/{scenario_id}/promote")
async def promote_scenario(
    scenario_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    _user=Depends(require_roles(["planner", "admin", "manager"])),
):
    """Mark a what-if scenario as the preferred plan (does not mutate live ERP schedule)."""
    tenant_id = tenant_ctx.get()
    scenario = await session.get(PlanningScenario, scenario_id)
    if not scenario or str(scenario.tenant_id) != tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NOT_FOUND", "message": "Scenario not found"})

    scenario.status = "promoted"
    await session.commit()
    return APIResponse(
        success=True,
        data={"scenario_id": str(scenario.id), "status": scenario.status, "name": scenario.name},
        error=None,
    )
