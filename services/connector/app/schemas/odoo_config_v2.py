"""Pydantic v2 schemas and JSON Schema for Odoo Config v2 (W1-03)."""

from __future__ import annotations

from typing import Any

import jsonschema
from pydantic import BaseModel, Field, field_validator, model_validator

FIELD_MAPPINGS_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": {
        "type": "array",
        "items": {
            "type": "object",
            "required": ["ipe_field", "odoo_model", "odoo_field"],
            "properties": {
                "ipe_field": {"type": "string", "minLength": 1},
                "odoo_model": {"type": "string", "minLength": 1},
                "odoo_field": {"type": "string", "minLength": 1},
                "transform": {"type": ["string", "null"]},
            },
            "additionalProperties": False,
        },
    },
}

DEFAULT_FIELD_MAPPINGS: dict[str, list[dict[str, str]]] = {
    "product": [
        {"ipe_field": "sku", "odoo_model": "product.product", "odoo_field": "default_code"},
        {"ipe_field": "name", "odoo_model": "product.product", "odoo_field": "name"},
    ],
    "manufacturing_order": [
        {"ipe_field": "erp_mo_id", "odoo_model": "mrp.production", "odoo_field": "name"},
        {"ipe_field": "quantity", "odoo_model": "mrp.production", "odoo_field": "product_qty"},
    ],
}


def validate_field_mappings(mappings: dict[str, Any]) -> dict[str, Any]:
    jsonschema.validate(instance=mappings, schema=FIELD_MAPPINGS_JSON_SCHEMA)
    return mappings


class FieldMappingItem(BaseModel):
    ipe_field: str = Field(min_length=1)
    odoo_model: str = Field(min_length=1)
    odoo_field: str = Field(min_length=1)
    transform: str | None = None


class OdooConfigCreateRequest(BaseModel):
    entity_key: str = Field(default="primary", min_length=1, max_length=64, pattern=r"^[a-zA-Z0-9_-]+$")
    name: str = Field(default="", max_length=128)
    odoo_url: str = Field(min_length=1, max_length=512)
    odoo_db: str = Field(min_length=1, max_length=128)
    odoo_username: str = Field(min_length=1, max_length=256)
    odoo_password: str | None = None
    enabled: bool = True
    sync_interval_minutes: int = Field(default=900, ge=1, le=10080)
    field_mappings: dict[str, list[FieldMappingItem]] = Field(default_factory=lambda: {})
    change_summary: str | None = None
    expected_version: int | None = None

    @field_validator("odoo_url")
    @classmethod
    def strip_url(cls, v: str) -> str:
        return v.rstrip("/")

    @field_validator("field_mappings")
    @classmethod
    def validate_mappings(cls, v: dict[str, list[FieldMappingItem]]) -> dict[str, list[FieldMappingItem]]:
        serializable = {
            entity: [item.model_dump() for item in items] for entity, items in v.items()
        }
        validate_field_mappings(serializable)
        return v

    @model_validator(mode="after")
    def fill_default_mappings(self) -> OdooConfigCreateRequest:
        if not self.field_mappings:
            self.field_mappings = {
                k: [FieldMappingItem(**item) for item in v] for k, v in DEFAULT_FIELD_MAPPINGS.items()
            }
        return self


class OdooConfigTestRequest(BaseModel):
    entity_key: str | None = None
    odoo_url: str | None = None
    odoo_db: str | None = None
    odoo_username: str | None = None
    odoo_password: str | None = None

    @field_validator("odoo_url")
    @classmethod
    def strip_url(cls, v: str | None) -> str | None:
        return v.rstrip("/") if v else v


class OdooConfigVersionSummary(BaseModel):
    entity_key: str
    version: int
    is_current: bool
    name: str
    odoo_url: str
    odoo_db: str
    odoo_username: str
    enabled: bool
    sync_interval_minutes: int
    password_set: bool
    field_mappings: dict[str, list[dict[str, Any]]]
    change_summary: str | None = None
    created_at: str | None = None


class OdooConfigListResponse(BaseModel):
    entities: list[OdooConfigVersionSummary]
    schema_version: int = 2


class OdooConnectionTestResult(BaseModel):
    connected: bool
    uid: int | None = None
    server_version: str | None = None
    latency_ms: float | None = None
    entity_key: str | None = None
