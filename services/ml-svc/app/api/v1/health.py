from fastapi import APIRouter

health_router = APIRouter(tags=["health"])


@health_router.get("/health")
async def health():
    return {"status": "ok", "service": "ml-svc"}
