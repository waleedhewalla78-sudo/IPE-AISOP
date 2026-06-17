from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
from ipe_shared.database.session import get_session
from ipe_shared.schemas.common import HealthResponse
from app.config import settings

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(
        status="ok",
        service=settings.SERVICE_NAME,
        version=settings.VERSION,
        timestamp=datetime.now(timezone.utc),
    )


@router.get("/ready", response_model=HealthResponse)
async def readiness(session: AsyncSession = Depends(get_session)):
    deps: dict[str, str] = {}
    try:
        from sqlalchemy import text
        await session.execute(text("SELECT 1"))
        deps["database"] = "ok"
    except Exception:
        deps["database"] = "down"
    status = "ok" if all(v == "ok" for v in deps.values()) else "degraded"
    return HealthResponse(
        status=status,
        service=settings.SERVICE_NAME,
        version=settings.VERSION,
        timestamp=datetime.now(timezone.utc),
        dependencies=deps,
    )
