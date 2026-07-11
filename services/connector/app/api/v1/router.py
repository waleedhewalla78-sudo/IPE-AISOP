from fastapi import APIRouter
from app.api.v1 import activate, health, sync, action, erp_odoo, odoo_config, erp_connections

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(sync.router)
api_router.include_router(action.router)
api_router.include_router(activate.router)
api_router.include_router(erp_odoo.router)
api_router.include_router(odoo_config.router)
api_router.include_router(erp_connections.router)
