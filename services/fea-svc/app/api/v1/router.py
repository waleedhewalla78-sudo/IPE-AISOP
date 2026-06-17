from fastapi import APIRouter

from app.api.v1 import feasibility, health

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(feasibility.router)
