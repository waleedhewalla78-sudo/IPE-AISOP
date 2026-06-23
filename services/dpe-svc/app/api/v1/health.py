from datetime import UTC, datetime

import httpx
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from ipe_shared.config import settings as shared_settings
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
        await session.execute(text("SELECT 1"))
        deps["database"] = "ok"
    except Exception:
        deps["database"] = "down"

    try:
        from aiokafka import AIOKafkaProducer

        producer = AIOKafkaProducer(bootstrap_servers=shared_settings.KAFKA_BOOTSTRAP_SERVERS)
        await producer.start()
        await producer.stop()
        deps["kafka"] = "ok"
    except Exception:
        deps["kafka"] = "down"

    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"{shared_settings.SCHEMA_REGISTRY_URL}/")
            if resp.status_code < 500:
                deps["schema_registry"] = "ok"
            else:
                deps["schema_registry"] = "down"
    except Exception:
        deps["schema_registry"] = "down"

    status = "ok" if all(v == "ok" for v in deps.values()) else "degraded"
    return HealthResponse(
        status=status,
        service=settings.SERVICE_NAME,
        version=settings.VERSION,
        timestamp=datetime.now(UTC),
        dependencies=deps,
    )
