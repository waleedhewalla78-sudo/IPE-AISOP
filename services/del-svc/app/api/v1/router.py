from fastapi import APIRouter

from app.api.v1 import delay, health, quality

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(delay.router)
api_router.include_router(quality.router)
