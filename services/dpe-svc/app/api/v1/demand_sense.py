from fastapi import APIRouter
from pydantic import BaseModel

from app.core.demand_sensing import disaggregate_weekly_forecast
from ipe_shared.middleware.tenant_context import tenant_ctx
from ipe_shared.schemas.common import APIResponse

router = APIRouter(prefix="/demand", tags=["demand"])


class SenseRequest(BaseModel):
    weekly_forecasts: list[float]
    historical_daily_pattern: list[float]


@router.post("/sense")
async def demand_sense(req: SenseRequest):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(
            success=False, data=None,
            error={"code": "NO_TENANT", "message": "No tenant context"},
        )

    daily_schedule = disaggregate_weekly_forecast(
        req.weekly_forecasts,
        req.historical_daily_pattern,
    )

    return APIResponse(
        success=True,
        data={
            "daily_schedule": daily_schedule,
            "weeks_processed": len(req.weekly_forecasts),
            "days_generated": len(daily_schedule),
        },
        error=None,
    )
