from fastapi import APIRouter

from app.api.v1 import analytics, capacity, health, iot, labor, project_plans, scenarios, utilisation

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(capacity.router)
api_router.include_router(utilisation.router)
api_router.include_router(analytics.router)
api_router.include_router(project_plans.router)
api_router.include_router(scenarios.router)
api_router.include_router(labor.router)
api_router.include_router(iot.router)
