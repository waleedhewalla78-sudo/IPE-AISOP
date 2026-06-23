from fastapi import APIRouter

from app.api.v1 import digital_twin

router = APIRouter()
router.include_router(digital_twin.router)