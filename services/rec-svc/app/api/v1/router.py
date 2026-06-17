from fastapi import APIRouter

from app.api.v1 import health, reconciliation

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(reconciliation.router)
