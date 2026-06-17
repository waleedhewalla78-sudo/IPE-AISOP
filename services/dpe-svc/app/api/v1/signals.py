from datetime import date, timedelta

from fastapi import APIRouter, Query

from app.core.external_signals.weather import WeatherSignalClient
from ipe_shared.middleware.tenant_context import tenant_ctx
from ipe_shared.schemas.common import APIResponse

router = APIRouter(prefix="/signals", tags=["signals"])

weather_client = WeatherSignalClient()


@router.get("/weather-adjustment")
async def weather_adjustment(
    work_center: str = Query(..., description="Work center location identifier"),
    days: int = Query(7, ge=1, le=30, description="Number of days to forecast"),
):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(
            success=False, data=None,
            error={"code": "NO_TENANT", "message": "No tenant context"},
        )

    today = date.today()
    adjustments = []
    for i in range(days):
        forecast_date = today + timedelta(days=i)
        factor = weather_client.get_capacity_adjustment_factor(work_center, forecast_date)
        adjustments.append({
            "date": forecast_date.isoformat(),
            "adjustment_factor": factor,
            "impact": "reduced" if factor < 1.0 else "normal",
        })

    return APIResponse(
        success=True,
        data={
            "work_center": work_center,
            "forecast_days": adjustments,
        },
        error=None,
    )
