from fastapi import APIRouter

from app.api.v1 import forecast, forecast_quality, health, signal_fusion_api

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(forecast.router)
api_router.include_router(forecast_quality.router)
api_router.include_router(signal_fusion_api.router)
