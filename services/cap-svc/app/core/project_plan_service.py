"""Persist project plans with version history."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ipe_shared.models.project_plan import ProjectPlan, ProjectPlanVersion


class ProjectPlanServiceError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


async def get_plan_by_code(session: AsyncSession, tenant_id: UUID, plan_code: str) -> ProjectPlan | None:
    result = await session.execute(
        select(ProjectPlan).where(
            ProjectPlan.tenant_id == tenant_id,
            ProjectPlan.plan_code == plan_code,
        )
    )
    return result.scalar_one_or_none()


async def list_plans(session: AsyncSession, tenant_id: UUID) -> list[dict]:
    result = await session.execute(
        select(ProjectPlan).where(ProjectPlan.tenant_id == tenant_id).order_by(ProjectPlan.plan_code)
    )
    plans = result.scalars().all()
    output = []
    for plan in plans:
        active = None
        if plan.active_version_id:
            ver_result = await session.execute(
                select(ProjectPlanVersion).where(ProjectPlanVersion.id == plan.active_version_id)
            )
            active = ver_result.scalar_one_or_none()
        output.append(_plan_summary(plan, active))
    return output


async def list_versions(session: AsyncSession, tenant_id: UUID, plan_code: str) -> list[dict]:
    plan = await get_plan_by_code(session, tenant_id, plan_code)
    if not plan:
        raise ProjectPlanServiceError("NOT_FOUND", f"Plan '{plan_code}' not found")

    result = await session.execute(
        select(ProjectPlanVersion)
        .where(ProjectPlanVersion.plan_id == plan.id, ProjectPlanVersion.tenant_id == tenant_id)
        .order_by(ProjectPlanVersion.version_number.desc())
    )
    return [_version_summary(v) for v in result.scalars().all()]


async def upload_plan_version(
    session: AsyncSession,
    tenant_id: UUID,
    uploaded_by: UUID | None,
    parsed: dict,
    file_name: str,
    mode: str,
    notes: str | None = None,
) -> dict:
    plan_code = parsed["plan_code"]
    existing = await get_plan_by_code(session, tenant_id, plan_code)

    if mode == "new" and existing:
        raise ProjectPlanServiceError(
            "PLAN_EXISTS",
            f"Plan '{plan_code}' already exists. Choose 'Update existing plan' to upload a new version.",
        )
    if mode == "update" and not existing:
        raise ProjectPlanServiceError(
            "PLAN_NOT_FOUND",
            f"Plan '{plan_code}' does not exist. Choose 'Create new plan' for first upload.",
        )

    if existing:
        dup = await session.execute(
            select(ProjectPlanVersion).where(
                ProjectPlanVersion.plan_id == existing.id,
                ProjectPlanVersion.file_sha256 == parsed["file_sha256"],
            )
        )
        if dup.scalar_one_or_none():
            raise ProjectPlanServiceError(
                "DUPLICATE_FILE",
                "This exact file was already uploaded for this plan.",
            )

    if not existing:
        existing = ProjectPlan(
            tenant_id=tenant_id,
            plan_code=plan_code,
            plan_name=parsed["plan_name"],
        )
        session.add(existing)
        await session.flush()
        next_version = 1
    else:
        existing.plan_name = parsed["plan_name"]
        existing.updated_at = datetime.now(UTC)
        max_ver = await session.execute(
            select(func.max(ProjectPlanVersion.version_number)).where(
                ProjectPlanVersion.plan_id == existing.id
            )
        )
        next_version = int(max_ver.scalar_one_or_none() or 0) + 1

    await session.execute(
        update(ProjectPlanVersion)
        .where(ProjectPlanVersion.plan_id == existing.id, ProjectPlanVersion.is_active.is_(True))
        .values(is_active=False)
    )

    version = ProjectPlanVersion(
        tenant_id=tenant_id,
        plan_id=existing.id,
        version_number=next_version,
        is_active=True,
        file_name=file_name,
        file_size_bytes=parsed["file_size_bytes"],
        file_sha256=parsed["file_sha256"],
        uploaded_by=uploaded_by,
        upload_notes=notes,
        operations=parsed["operations"],
        validation_summary={
            "row_count": parsed["row_count"],
            "schema_version": "1.0",
        },
    )
    session.add(version)
    await session.flush()

    existing.active_version_id = version.id
    await session.commit()
    await session.refresh(existing)
    await session.refresh(version)

    return {
        "plan": _plan_summary(existing, version),
        "version": _version_summary(version),
        "message": f"Plan '{plan_code}' version {next_version} uploaded successfully.",
    }


async def activate_version(
    session: AsyncSession,
    tenant_id: UUID,
    plan_code: str,
    version_id: UUID,
) -> dict:
    plan = await get_plan_by_code(session, tenant_id, plan_code)
    if not plan:
        raise ProjectPlanServiceError("NOT_FOUND", f"Plan '{plan_code}' not found")

    result = await session.execute(
        select(ProjectPlanVersion).where(
            ProjectPlanVersion.id == version_id,
            ProjectPlanVersion.plan_id == plan.id,
            ProjectPlanVersion.tenant_id == tenant_id,
        )
    )
    version = result.scalar_one_or_none()
    if not version:
        raise ProjectPlanServiceError("NOT_FOUND", "Version not found for this plan")

    await session.execute(
        update(ProjectPlanVersion)
        .where(ProjectPlanVersion.plan_id == plan.id)
        .values(is_active=False)
    )
    version.is_active = True
    plan.active_version_id = version.id
    plan.updated_at = datetime.now(UTC)
    await session.commit()

    return {
        "plan": _plan_summary(plan, version),
        "message": f"Activated version {version.version_number} for plan '{plan_code}'.",
    }


async def get_active_schedule(session: AsyncSession, tenant_id: UUID, plan_code: str) -> dict:
    plan = await get_plan_by_code(session, tenant_id, plan_code)
    if not plan or not plan.active_version_id:
        raise ProjectPlanServiceError("NOT_FOUND", f"No active version for plan '{plan_code}'")

    result = await session.execute(
        select(ProjectPlanVersion).where(ProjectPlanVersion.id == plan.active_version_id)
    )
    version = result.scalar_one_or_none()
    if not version:
        raise ProjectPlanServiceError("NOT_FOUND", "Active version record missing")

    return operations_to_gantt(version)


def operations_to_gantt(version: ProjectPlanVersion) -> dict:
    mo_map: dict[str, dict] = {}
    for op in version.operations or []:
        mo_id = op["mo_id"]
        if mo_id not in mo_map:
            mo_map[mo_id] = {
                "mo_id": mo_id,
                "mo_name": mo_id,
                "operations": [],
            }
        status = op.get("status", "planned")
        mo_map[mo_id]["operations"].append(
            {
                "id": f"{mo_id}-{op['operation_sequence']}",
                "mo_id": mo_id,
                "mo_name": mo_id,
                "sequence": op["operation_sequence"],
                "work_center_id": op["work_center_code"],
                "work_center_name": op["work_center_code"],
                "planned_start": op["start_minute"],
                "planned_end": op["end_minute"],
                "duration": op["duration_minutes"],
                "status": status,
                "is_frozen": status == "frozen",
                "is_disrupted": status == "disrupted",
            }
        )

    rows = list(mo_map.values())
    for row in rows:
        row["operations"].sort(key=lambda x: x["sequence"])

    return {
        "plan_code": version.operations[0]["plan_code"] if version.operations else "",
        "version_number": version.version_number,
        "version_id": str(version.id),
        "rows": rows,
    }


def _plan_summary(plan: ProjectPlan, active: ProjectPlanVersion | None) -> dict:
    return {
        "plan_code": plan.plan_code,
        "plan_name": plan.plan_name,
        "active_version_id": str(plan.active_version_id) if plan.active_version_id else None,
        "active_version_number": active.version_number if active else None,
        "operation_count": len(active.operations) if active and active.operations else 0,
        "updated_at": plan.updated_at.isoformat() if plan.updated_at else None,
    }


def _version_summary(version: ProjectPlanVersion) -> dict:
    return {
        "id": str(version.id),
        "version_number": version.version_number,
        "is_active": version.is_active,
        "file_name": version.file_name,
        "file_size_bytes": version.file_size_bytes,
        "row_count": len(version.operations or []),
        "uploaded_at": version.created_at.isoformat() if version.created_at else None,
        "upload_notes": version.upload_notes,
    }
