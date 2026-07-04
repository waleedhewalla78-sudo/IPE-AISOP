"""
Tenant resource quota enforcement.
Checked before creating new resources (MOs, BOMs, products, etc.).
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ipe_shared.config import settings

logger = logging.getLogger(__name__)

DEFAULT_QUOTAS = {
    "max_manufacturing_orders": 1000,
    "max_boms": 500,
    "max_routings": 500,
    "max_products": 2000,
    "max_inventory_items": 5000,
    "max_users": 50,
}

RESOURCE_TYPES = frozenset(
    {
        "manufacturing_orders",
        "boms",
        "routings",
        "products",
        "inventory_items",
        "users",
    }
)


@dataclass
class TenantQuota:
    max_manufacturing_orders: int
    max_boms: int
    max_routings: int
    max_products: int
    max_inventory_items: int
    max_users: int


class QuotaExceededError(Exception):
    """Raised when a tenant has reached a resource limit (non-HTTP contexts)."""

    def __init__(self, tenant_id: str, resource_type: str, current_count: int, max_allowed: int):
        self.tenant_id = tenant_id
        self.resource_type = resource_type
        self.current_count = current_count
        self.max_allowed = max_allowed
        super().__init__(
            f"Tenant {tenant_id} has reached {resource_type} quota "
            f"({current_count}/{max_allowed})"
        )


def _quota_overrides_path() -> Path:
    configured = getattr(settings, "TENANT_QUOTA_OVERRIDES", "") or "config/tenant-quotas.json"
    return Path(configured)


def _load_quota_overrides() -> dict:
    path = _quota_overrides_path()
    try:
        with path.open(encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}


def get_quota(tenant_id: str) -> TenantQuota:
    """Get effective quota for a tenant (default + overrides)."""
    quota = DEFAULT_QUOTAS.copy()
    overrides = _load_quota_overrides()
    tenant_overrides = overrides.get(tenant_id)
    if isinstance(tenant_overrides, dict):
        quota.update(tenant_overrides)
    return TenantQuota(**quota)


def _max_for_resource(quota: TenantQuota, resource_type: str) -> int | None:
    if resource_type not in RESOURCE_TYPES:
        return None
    return getattr(quota, f"max_{resource_type}")


async def check_quota(tenant_id: str, resource_type: str, current_count: int) -> bool:
    """
    Check if tenant can create one more of the given resource.
    Returns True if under quota, False if at or over limit.
    """
    quota = get_quota(tenant_id)
    max_allowed = _max_for_resource(quota, resource_type)
    if max_allowed is None:
        return True
    return current_count < max_allowed


async def assert_quota(tenant_id: str, resource_type: str, current_count: int) -> None:
    """Raise QuotaExceededError if tenant cannot create another resource."""
    if not await check_quota(tenant_id, resource_type, current_count):
        quota = get_quota(tenant_id)
        max_allowed = _max_for_resource(quota, resource_type) or 0
        raise QuotaExceededError(tenant_id, resource_type, current_count, max_allowed)


async def count_tenant_resource(
    session: AsyncSession,
    tenant_id: UUID | str,
    resource_type: str,
) -> int:
    """Count existing resources of a type for a tenant."""
    from ipe_shared.models.bom import BillOfMaterial
    from ipe_shared.models.inventory import InventoryPosition
    from ipe_shared.models.manufacturing_order import ManufacturingOrder
    from ipe_shared.models.product import Product
    from ipe_shared.models.routing import RoutingOperation
    from ipe_shared.models.user import User

    models = {
        "manufacturing_orders": ManufacturingOrder,
        "boms": BillOfMaterial,
        "routings": RoutingOperation,
        "products": Product,
        "inventory_items": InventoryPosition,
        "users": User,
    }
    model = models.get(resource_type)
    if model is None:
        return 0

    tid = tenant_id if isinstance(tenant_id, UUID) else UUID(str(tenant_id))
    stmt = select(func.count()).select_from(model).where(model.tenant_id == tid)
    result = await session.execute(stmt)
    return int(result.scalar_one() or 0)


async def enforce_quota(tenant_id: str, resource_type: str, current_count: int) -> None:
    """
    Raises HTTPException(429) if tenant is over quota.
    Use in service endpoints before creating resources.
    """
    try:
        await assert_quota(tenant_id, resource_type, current_count)
    except QuotaExceededError as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc
