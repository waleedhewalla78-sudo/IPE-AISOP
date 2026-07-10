from fastapi import APIRouter

from app.api.v1 import forecast, forecast_quality, health

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(forecast.router)
api_router.include_router(forecast_quality.router)
