from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select as sa_select
from sqlalchemy.ext.asyncio import AsyncSession

from ipe_shared.database.session import get_session as get_db_session
from ipe_shared.middleware.tenant_context import tenant_ctx
from ipe_shared.models.shift import Shift
from ipe_shared.models.skill import Skill
from ipe_shared.models.worker import Worker
from ipe_shared.schemas.common import APIResponse

router = APIRouter(prefix="/labor", tags=["labor"])


class SkillCreate(BaseModel):
    name: str
    description: str | None = None
    category: str = "general"
    certification_required: bool = False


class WorkerCreate(BaseModel):
    erp_source_id: str
    name: str
    shift_calendar_id: UUID | None = None
    skill_ids: list[UUID] = []
    cost_per_hour: float | None = None
    overtime_eligible: bool = True


class ShiftCreate(BaseModel):
    name: str
    description: str | None = None
    days_of_week: list[int] = [0, 1, 2, 3, 4]
    start_hour: int = 8
    start_minute: int = 0
    end_hour: int = 16
    end_minute: int = 0
    break_minutes: int = 30
    timezone: str = "UTC"


@router.get("/skills")
async def list_skills(session: AsyncSession = Depends(get_db_session)):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})

    result = await session.execute(
        sa_select(Skill).where(Skill.tenant_id == UUID(tenant_id))
    )
    skills = result.scalars().all()
    return APIResponse(success=True, data=[
        {"id": str(s.id), "name": s.name, "category": s.category, "certification_required": s.certification_required}
        for s in skills
    ], error=None)


@router.post("/skills")
async def create_skill(req: SkillCreate, session: AsyncSession = Depends(get_db_session)):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})

    skill = Skill(
        tenant_id=UUID(tenant_id),
        name=req.name,
        description=req.description,
        category=req.category,
        certification_required=req.certification_required,
    )
    session.add(skill)
    await session.flush()
    return APIResponse(success=True, data={"id": str(skill.id), "name": skill.name}, error=None)


@router.get("/workers")
async def list_workers(session: AsyncSession = Depends(get_db_session)):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})

    result = await session.execute(
        sa_select(Worker).where(Worker.tenant_id == UUID(tenant_id))
    )
    workers = result.scalars().all()
    return APIResponse(success=True, data=[
        {
            "id": str(w.id),
            "erp_source_id": w.erp_source_id,
            "name": w.name,
            "is_active": bool(w.is_active),
            "overtime_eligible": bool(w.overtime_eligible),
        }
        for w in workers
    ], error=None)


@router.post("/workers")
async def create_worker(req: WorkerCreate, session: AsyncSession = Depends(get_db_session)):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})

    worker = Worker(
        tenant_id=UUID(tenant_id),
        erp_source_id=req.erp_source_id,
        name=req.name,
        shift_calendar_id=req.shift_calendar_id,
        cost_per_hour=req.cost_per_hour,
        overtime_eligible=req.overtime_eligible,
    )
    session.add(worker)
    await session.flush()
    return APIResponse(success=True, data={"id": str(worker.id), "name": worker.name}, error=None)


@router.get("/shifts")
async def list_shifts(session: AsyncSession = Depends(get_db_session)):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})

    result = await session.execute(
        sa_select(Shift).where(Shift.tenant_id == UUID(tenant_id))
    )
    shifts = result.scalars().all()
    return APIResponse(success=True, data=[
        {
            "id": str(s.id),
            "name": s.name,
            "days_of_week": s.days_of_week,
            "start_hour": s.start_hour,
            "end_hour": s.end_hour,
            "break_minutes": s.break_minutes,
        }
        for s in shifts
    ], error=None)


@router.post("/shifts")
async def create_shift(req: ShiftCreate, session: AsyncSession = Depends(get_db_session)):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})

    shift = Shift(
        tenant_id=UUID(tenant_id),
        name=req.name,
        description=req.description,
        days_of_week=req.days_of_week,
        start_hour=req.start_hour,
        start_minute=req.start_minute,
        end_hour=req.end_hour,
        end_minute=req.end_minute,
        break_minutes=req.break_minutes,
        timezone=req.timezone,
    )
    session.add(shift)
    await session.flush()
    return APIResponse(success=True, data={"id": str(shift.id), "name": shift.name}, error=None)
