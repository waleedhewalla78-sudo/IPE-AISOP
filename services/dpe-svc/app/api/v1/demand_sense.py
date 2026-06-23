from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.demand_sensing import disaggregate_weekly_forecast
from ipe_shared.auth.rbac import require_roles
from ipe_shared.middleware.tenant_context import tenant_ctx
from ipe_shared.schemas.common import APIResponse
from ipe_shared.schemas.xai import XAIExplanation

router = APIRouter(prefix="/demand", tags=["demand"])


class SenseRequest(BaseModel):
    weekly_forecasts: list[float]
    historical_daily_pattern: list[float]


@router.post("/sense")
async def demand_sense(
    req: SenseRequest,
    current_user=Depends(require_roles(["admin", "planner"])),
):
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
            "xai_explanation": XAIExplanation(
                constraints=["historical_pattern_weighted_disaggregation"],
                assumptions=["weekly_forecasts_accurate", "historical_pattern_representative"],
                confidence_score=round(min(1.0, len(req.historical_daily_pattern) / 7.0) if req.historical_daily_pattern else 0.3, 4),
                contributing_factors={
                    "pattern_coverage": round(min(1.0, len(req.historical_daily_pattern) / 7.0), 4),
                    "forecast_weeks": round(len(req.weekly_forecasts) / 52.0, 4),
                },
            ).model_dump(),
        },
        error=None,
    )
