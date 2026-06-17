from datetime import datetime, timezone
from fastapi import APIRouter
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
