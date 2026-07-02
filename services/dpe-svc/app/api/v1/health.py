from fastapi import APIRouter

from app.config import settings
from ipe_shared.health.endpoints import register_health_routes

router = APIRouter(tags=["health"])
register_health_routes(router, settings)
