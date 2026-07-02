"""Shared FastAPI health route helpers."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Protocol

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ipe_shared.database.session import get_session
from ipe_shared.health.probes import collect_dependencies, overall_status, uptime_seconds
from ipe_shared.schemas.common import HealthResponse


class ServiceSettings(Protocol):
    SERVICE_NAME: str
    VERSION: str


def register_health_routes(router: APIRouter, service_settings: ServiceSettings) -> None:
    @router.get("/health", response_model=HealthResponse)
    async def health(session: AsyncSession = Depends(get_session)):
        deps = await collect_dependencies(session)
        status = overall_status(deps)
        return HealthResponse(
            status=status,
            service=service_settings.SERVICE_NAME,
            version=service_settings.VERSION,
            timestamp=datetime.now(UTC),
            uptime_seconds=uptime_seconds(),
            dependencies=deps,
        )

    @router.get("/ready", response_model=HealthResponse)
    async def readiness(session: AsyncSession = Depends(get_session)):
        deps = await collect_dependencies(session)
        db_ok = deps.get("database", {}).get("status") == "up"
        status = "ok" if db_ok else "degraded"
        return HealthResponse(
            status=status,
            service=service_settings.SERVICE_NAME,
            version=service_settings.VERSION,
            timestamp=datetime.now(UTC),
            uptime_seconds=uptime_seconds(),
            dependencies=deps,
        )
