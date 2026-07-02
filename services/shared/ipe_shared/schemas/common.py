from datetime import datetime
from typing import Generic, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    success: bool = True
    data: T | None = None
    error: Optional["APIError"] = None
    meta: Optional["APIMeta"] = None


class APIError(BaseModel):
    code: str
    message: str
    details: dict | None = None


class APIMeta(BaseModel):
    total: int | None = None
    offset: int | None = None
    limit: int | None = None
    processing_time_ms: int | None = None


class HealthResponse(BaseModel):
    status: str = "ok"
    service: str
    version: str
    timestamp: datetime
    uptime_seconds: int | None = None
    dependencies: dict = {}


class PaginationParams(BaseModel):
    offset: int = 0
    limit: int = 50
