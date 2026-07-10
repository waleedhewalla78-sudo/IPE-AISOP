from fastapi import APIRouter

from app.api.v1 import health, material, safety_stock_api, segmentation, supply_chain

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(material.router)
api_router.include_router(supply_chain.router)
api_router.include_router(segmentation.router)
api_router.include_router(safety_stock_api.router)
