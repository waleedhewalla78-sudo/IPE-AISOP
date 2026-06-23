"""Feature flags API endpoints."""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from ipe_shared.feature_flags.flags import get_feature_flags

router = APIRouter(prefix="/feature-flags", tags=["feature-flags"])


class FlagToggleRequest(BaseModel):
    enabled: bool


@router.get("/")
async def list_flags() -> dict:
    flags = get_feature_flags()
    return {"flags": flags.list_flags()}


@router.get("/{flag_name}")
async def get_flag(flag_name: str) -> dict:
    flags = get_feature_flags()
    return {"flag_name": flag_name, "enabled": flags.is_enabled(flag_name)}


@router.post("/{flag_name}/toggle")
async def toggle_flag(flag_name: str, body: FlagToggleRequest) -> dict:
    flags = get_feature_flags()
    flags.set_enabled(flag_name, body.enabled)
    return {"flag_name": flag_name, "enabled": body.enabled}


@router.get("/autonomy/{tenant_id}")
async def get_autonomy_flags(tenant_id: str) -> dict:
    flags = get_feature_flags()
    return {
        "tenant_id": tenant_id,
        "shadow": flags.is_enabled("ipe.autonomy.shadow"),
        "suggest": flags.is_enabled("ipe.autonomy.suggest"),
        "autonomous": flags.is_enabled("ipe.autonomy.autonomous"),
    }
