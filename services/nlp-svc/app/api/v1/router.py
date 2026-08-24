from fastapi import APIRouter

from app.api.v1 import contextual, copilot, governance, health, reports

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(copilot.router)
api_router.include_router(governance.router)
api_router.include_router(reports.router)
api_router.include_router(contextual.router)
