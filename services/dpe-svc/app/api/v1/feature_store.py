"""Feature Store API endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from ipe_shared.ml.feature_store import IPE_FEATURES, get_feature_store

router = APIRouter(prefix="/ml/features", tags=["ml-ops"])


class FeatureRequest(BaseModel):
    feature_name: str = Field(..., min_length=1)
    entity_value: str = Field(..., min_length=1)


class SetFeatureRequest(BaseModel):
    feature_name: str = Field(..., min_length=1)
    entity_key: str = Field(..., min_length=1)
    entity_value: str = Field(..., min_length=1)
    value: float | str | int


@router.get("/")
async def list_features() -> dict:
    store = get_feature_store()
    return {"features": store.list_features()}


@router.get("/{feature_name}/{entity_value}")
async def get_feature(feature_name: str, entity_value: str) -> dict:
    store = get_feature_store()
    value = store.get_feature(feature_name, entity_value)
    return {"feature_name": feature_name, "entity_value": entity_value, "value": value}


@router.post("/set")
async def set_feature(body: SetFeatureRequest) -> dict:
    store = get_feature_store()
    store.set_feature(body.feature_name, body.entity_key, body.entity_value, body.value)
    return {"feature_name": body.feature_name, "entity_value": body.entity_value, "stored": True}


@router.get("/entity/{entity_value}")
async def get_entity_features(entity_value: str) -> dict:
    store = get_feature_store()
    features = store.get_entity_features(entity_value)
    return {"entity_value": entity_value, "features": features}


@router.get("/stats")
async def get_feature_store_stats() -> dict:
    store = get_feature_store()
    return {
        "total_features": len(IPE_FEATURES),
        "total_cached": len(store._features),
        "expired_count": store.get_expired_count(),
    }
