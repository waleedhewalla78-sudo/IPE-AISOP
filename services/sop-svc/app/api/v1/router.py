from fastapi import APIRouter

from app.api.v1 import consensus, health, sop, versions

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(sop.router)
api_router.include_router(consensus.router)
api_router.include_router(versions.router)
