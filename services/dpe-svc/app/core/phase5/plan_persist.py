"""Optional durable snapshots for MPS/MRP compute runs (Spec 029)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from ipe_shared.models.mps_mrp_run import MpsRun, MrpRun


def _parse_tenant(tenant_id: str) -> UUID | None:
    try:
        return UUID(str(tenant_id))
    except Exception:
        return None


async def save_mps_run(
    session: AsyncSession,
    *,
    tenant_id: str,
    product_id: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    tid = _parse_tenant(tenant_id)
    if tid is None:
        return {"persisted": False, "error": "invalid_tenant_id"}
    row = MpsRun(tenant_id=tid, product_id=str(product_id), run_payload=payload)
    session.add(row)
    try:
        await session.commit()
    except Exception as exc:
        try:
            await session.rollback()
        except Exception:
            pass
        return {"persisted": False, "error": str(exc)}
    return {"persisted": True, "id": str(getattr(row, "id", "")), "product_id": product_id}


async def save_mrp_run(
    session: AsyncSession,
    *,
    tenant_id: str,
    root_product_id: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    tid = _parse_tenant(tenant_id)
    if tid is None:
        return {"persisted": False, "error": "invalid_tenant_id"}
    row = MrpRun(tenant_id=tid, root_product_id=str(root_product_id), run_payload=payload)
    session.add(row)
    try:
        await session.commit()
    except Exception as exc:
        try:
            await session.rollback()
        except Exception:
            pass
        return {"persisted": False, "error": str(exc)}
    return {
        "persisted": True,
        "id": str(getattr(row, "id", "")),
        "root_product_id": root_product_id,
    }
