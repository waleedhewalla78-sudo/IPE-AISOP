"""Notify connector when a resolution scenario is approved (Odoo write-back)."""

from __future__ import annotations

import logging
import os

import httpx

from ipe_shared.models.manufacturing_order import ManufacturingOrder
from ipe_shared.models.resolution import ResolutionScenario

logger = logging.getLogger(__name__)


async def notify_odoo_resolution(
    scenario: ResolutionScenario,
    mo: ManufacturingOrder,
    tenant_id: str,
) -> None:
    connector_url = os.getenv("CONNECTOR_SVC_URL", "http://connector:8009").rstrip("/")
    payload = {
        "mo_id": str(scenario.mo_id),
        "erp_mo_id": mo.erp_mo_id,
        "scenario_id": str(scenario.id),
        "strategy": scenario.strategy,
        "approved_by": scenario.approved_by or "system",
        "comment": scenario.comment or "",
        "delivery_impact_days": float(scenario.delivery_impact_days) if scenario.delivery_impact_days else None,
        "cost_impact": float(scenario.cost_impact) if scenario.cost_impact else None,
    }
    headers = {"X-Tenant-ID": tenant_id, "Content-Type": "application/json"}
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"{connector_url}/api/v1/erp/odoo/resolution-notify",
                json=payload,
                headers=headers,
            )
            if resp.status_code >= 400:
                logger.warning("Odoo resolution notify HTTP %s: %s", resp.status_code, resp.text[:200])
    except Exception:
        logger.exception("Odoo resolution notify failed (non-blocking)")
