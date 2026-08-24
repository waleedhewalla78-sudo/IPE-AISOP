from fastapi import APIRouter

from app.api.v1 import data_upload, health, upload

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(upload.router)
api_router.include_router(data_upload.router)
