from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from ipe_shared.database.session import get_session
from ipe_shared.schemas.common import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(
        status="ok",
        service=settings.SERVICE_NAME,
        version=settings.VERSION,
        timestamp=datetime.now(UTC),
    )


@router.get("/ready", response_model=HealthResponse)
async def readiness(session: AsyncSession = Depends(get_session)):
    deps = {}
    try:
        from sqlalchemy import text

        await session.execute(text("SELECT 1"))
        deps["database"] = "ok"
    except Exception:
        deps["database"] = "down"
    status = "ok" if deps.get("database") == "ok" else "degraded"
    return HealthResponse(
        status=status,
        service=settings.SERVICE_NAME,
        version=settings.VERSION,
        timestamp=datetime.now(UTC),
        dependencies=deps,
    )
