from fastapi import APIRouter

from app.api.v1 import admin, analytics, demand, demand_sense, health, signals

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(demand.router)
api_router.include_router(admin.router)
api_router.include_router(analytics.router)
api_router.include_router(demand_sense.router)
api_router.include_router(signals.router)
