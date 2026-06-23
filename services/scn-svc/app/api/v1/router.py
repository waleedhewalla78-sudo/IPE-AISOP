from fastapi import APIRouter

from app.api.v1 import health, scn
from ipe_shared.auth.scim import router as scim_router

router = APIRouter()
router.include_router(health.router)
router.include_router(scn.router)
router.include_router(scim_router)