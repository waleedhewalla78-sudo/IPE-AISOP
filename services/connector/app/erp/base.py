"""ERP connector interface — mock, SAP, and D365 scaffolds."""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class ERPResult:
    success: bool
    message: str
    external_id: str | None = None


@dataclass
class Material:
    id: str
    name: str
    unit: str


@dataclass
class ProductionOrder:
    id: str
    product_id: str
    quantity: float
    status: str


@dataclass
class Schedule:
    mo_ids: list[str]
    metadata: dict[str, Any]


class ERPConnector(ABC):
    @abstractmethod
    async def publish_schedule(self, tenant_id: str, schedule: Schedule) -> ERPResult:
        ...

    @abstractmethod
    async def fetch_material_master(self, tenant_id: str) -> list[Material]:
        ...

    @abstractmethod
    async def fetch_production_orders(self, tenant_id: str) -> list[ProductionOrder]:
        ...

    @abstractmethod
    async def confirm_order(self, tenant_id: str, order_id: str) -> ERPResult:
        ...


class MockERPConnector(ERPConnector):
    async def publish_schedule(self, tenant_id: str, schedule: Schedule) -> ERPResult:
        return ERPResult(success=True, message="Mock schedule queued", external_id="mock-sched-001")

    async def fetch_material_master(self, tenant_id: str) -> list[Material]:
        return [Material(id="MAT-001", name="Demo Material", unit="EA")]

    async def fetch_production_orders(self, tenant_id: str) -> list[ProductionOrder]:
        return [ProductionOrder(id="MO-001", product_id="MAT-001", quantity=100, status="released")]

    async def confirm_order(self, tenant_id: str, order_id: str) -> ERPResult:
        return ERPResult(success=True, message=f"Mock confirmed {order_id}", external_id=order_id)


class SAPConnector(ERPConnector):
    """POST-B: wire SAP RFC/ODATA (BAPI_PRODORD_CREATE, MD04, etc.)."""

    async def publish_schedule(self, tenant_id: str, schedule: Schedule) -> ERPResult:
        raise NotImplementedError("SAP RFC credentials required (POST-B)")

    async def fetch_material_master(self, tenant_id: str) -> list[Material]:
        raise NotImplementedError("SAP ODATA /MDM read required (POST-B)")

    async def fetch_production_orders(self, tenant_id: str) -> list[ProductionOrder]:
        raise NotImplementedError("SAP PP read required (POST-B)")

    async def confirm_order(self, tenant_id: str, order_id: str) -> ERPResult:
        raise NotImplementedError("SAP confirmation BAPI required (POST-B)")


class D365Connector(ERPConnector):
    """POST-B: wire D365 Finance & Operations REST APIs."""

    async def publish_schedule(self, tenant_id: str, schedule: Schedule) -> ERPResult:
        raise NotImplementedError("D365 OAuth + production order API required (POST-B)")

    async def fetch_material_master(self, tenant_id: str) -> list[Material]:
        raise NotImplementedError("D365 ReleasedProductsV2 required (POST-B)")

    async def fetch_production_orders(self, tenant_id: str) -> list[ProductionOrder]:
        raise NotImplementedError("D365 ProductionOrderHeaders required (POST-B)")

    async def confirm_order(self, tenant_id: str, order_id: str) -> ERPResult:
        raise NotImplementedError("D365 confirmation endpoint required (POST-B)")


def get_erp_connector() -> ERPConnector:
    provider = os.getenv("ERP_PROVIDER", "mock").lower()
    if provider == "sap":
        return SAPConnector()
    if provider == "d365":
        return D365Connector()
    return MockERPConnector()
