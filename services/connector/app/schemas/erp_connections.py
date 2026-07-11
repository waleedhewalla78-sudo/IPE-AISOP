"""Pydantic schemas for ERP connection management (W1-04)."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class ErpConnectionCreate(BaseModel):
    erp_type: str = Field(default="odoo", max_length=20)
    display_name: str = Field(min_length=1, max_length=100)
    host_url: str = Field(min_length=1, max_length=500)
    database_name: str = Field(min_length=1, max_length=100)
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1)
    is_production: bool = False
    sync_interval_seconds: int = Field(default=900, ge=60, le=86400)
    sync_enabled: bool = True
    api_protocol: str = Field(default="xmlrpc", max_length=20)

    @field_validator("host_url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        v = v.strip().rstrip("/")
        if not (v.startswith("http://") or v.startswith("https://")):
            raise ValueError("host_url must start with http:// or https://")
        return v

    @field_validator("erp_type")
    @classmethod
    def validate_erp_type(cls, v: str) -> str:
        allowed = {"odoo", "sapb1"}
        if v not in allowed:
            raise ValueError(f"erp_type must be one of {allowed}")
        return v


class ErpConnectionUpdate(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=100)
    host_url: str | None = Field(default=None, min_length=1, max_length=500)
    database_name: str | None = Field(default=None, min_length=1, max_length=100)
    username: str | None = Field(default=None, min_length=1, max_length=100)
    password: str | None = None
    sync_interval_seconds: int | None = Field(default=None, ge=60, le=86400)
    sync_enabled: bool | None = None
    is_production: bool | None = None

    @field_validator("host_url")
    @classmethod
    def validate_url(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip().rstrip("/")
        if not (v.startswith("http://") or v.startswith("https://")):
            raise ValueError("host_url must start with http:// or https://")
        return v


class ErpConnectionResponse(BaseModel):
    id: UUID
    display_name: str
    host_url: str
    database_name: str
    username: str
    erp_type: str
    is_active: bool
    is_production: bool
    last_test_at: datetime | None = None
    last_test_result: str | None = None
    last_test_message: str | None = None
    sync_interval_seconds: int
    sync_enabled: bool
    api_protocol: str = "xmlrpc"
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class ErpConnectionTestResult(BaseModel):
    result: str  # success | auth_failed | unreachable | timeout
    message: str
    response_time_ms: float | None = None
    odoo_version: str | None = None
    databases_available: list[str] | None = None


class ErpConnectionLogEntry(BaseModel):
    id: UUID
    action: str
    result: str | None = None
    details: dict[str, Any] | None = None
    performed_by: UUID | None = None
    performed_at: datetime | None = None

    model_config = {"from_attributes": True}


class SyncNowResponse(BaseModel):
    sync_run_id: UUID | str
    status: str = "started"
