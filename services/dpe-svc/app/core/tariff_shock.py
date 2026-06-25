"""Tariff shock simulation and exposure analysis."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ipe_shared.models.activity_cost import ActivityCostDriver
from ipe_shared.models.bom import BillOfMaterial, BomLine
from ipe_shared.models.landed_cost import LandedCostProfile
from ipe_shared.models.manufacturing_order import ManufacturingOrder
from ipe_shared.models.material_attributes import MaterialAttribute
from ipe_shared.models.product import Product
from ipe_shared.models.tenant import Tenant

from app.core.margin_priority import compute_margin_adjusted_priority


@dataclass
class TariffExposureRow:
    region: str
    material_count: int
    mo_count: int
    total_exposure_usd: float


async def _get_substitute_map(session: AsyncSession, tenant_id: UUID) -> dict[str, str]:
    result = await session.execute(select(Tenant.config).where(Tenant.id == tenant_id))
    row = result.fetchone()
    config = dict(row[0]) if row and row[0] else {}
    mapping = config.get("substitute_materials") or {}
    return {str(k): str(v) for k, v in mapping.items()}


async def _materials_in_region(
    session: AsyncSession,
    tenant_id: UUID,
    region: str,
) -> list[UUID]:
    result = await session.execute(
        select(MaterialAttribute.material_id).where(
            MaterialAttribute.tenant_id == tenant_id,
            MaterialAttribute.attributes["origin_region"].astext == region,
        )
    )
    return [row[0] for row in result.fetchall()]


async def _mos_using_materials(
    session: AsyncSession,
    tenant_id: UUID,
    material_ids: list[UUID],
) -> list[ManufacturingOrder]:
    if not material_ids:
        return []

    bom_ids_result = await session.execute(
        select(BomLine.bom_id)
        .join(BillOfMaterial, BomLine.bom_id == BillOfMaterial.id)
        .where(
            BillOfMaterial.tenant_id == tenant_id,
            BomLine.component_id.in_(material_ids),
        )
        .distinct()
    )
    bom_ids = [row[0] for row in bom_ids_result.fetchall()]
    if not bom_ids:
        return []

    mo_result = await session.execute(
        select(ManufacturingOrder).where(
            ManufacturingOrder.tenant_id == tenant_id,
            ManufacturingOrder.bom_id.in_(bom_ids),
            ManufacturingOrder.status.in_(("planned", "confirmed", "in_progress")),
        )
    )
    return list(mo_result.scalars().all())


def _estimate_tariff_cost_delta(
    profile: LandedCostProfile,
    mo_qty: float,
    bom_qty_per: float,
    tariff_delta_pct: float,
) -> float:
    base = float(profile.base_cost_usd or 0)
    component_qty = mo_qty * bom_qty_per
    return base * (tariff_delta_pct / 100.0) * component_qty


async def get_tariff_exposure(
    session: AsyncSession,
    tenant_id: UUID,
) -> list[TariffExposureRow]:
    """Summarize tariff exposure by origin region."""
    attr_result = await session.execute(
        select(MaterialAttribute).where(MaterialAttribute.tenant_id == tenant_id)
    )
    attrs = list(attr_result.scalars().all())
    if not attrs:
        return []

    regions: dict[str, list[UUID]] = {}
    for attr in attrs:
        region = (attr.attributes or {}).get("origin_region")
        if not region:
            continue
        regions.setdefault(region, []).append(attr.material_id)

    rows: list[TariffExposureRow] = []
    for region, material_ids in regions.items():
        profile_result = await session.execute(
            select(LandedCostProfile).where(
                LandedCostProfile.tenant_id == tenant_id,
                LandedCostProfile.region == region,
            )
        )
        profile = profile_result.scalar_one_or_none()
        mos = await _mos_using_materials(session, tenant_id, material_ids)
        exposure = 0.0
        if profile:
            base = float(profile.base_cost_usd or 0)
            tariff_pct = float(profile.tariff_pct or 0)
            for mo in mos:
                bom_line_result = await session.execute(
                    select(BomLine)
                    .join(BillOfMaterial, BomLine.bom_id == BillOfMaterial.id)
                    .where(
                        BillOfMaterial.tenant_id == tenant_id,
                        BomLine.bom_id == mo.bom_id,
                        BomLine.component_id.in_(material_ids),
                    )
                )
                for line in bom_line_result.scalars().all():
                    exposure += base * (tariff_pct / 100.0) * float(mo.quantity or 1) * float(line.quantity_per or 1)

        rows.append(
            TariffExposureRow(
                region=region,
                material_count=len(material_ids),
                mo_count=len(mos),
                total_exposure_usd=round(exposure, 2),
            )
        )
    return rows


async def run_tariff_shock(
    session: AsyncSession,
    tenant_id: UUID,
    *,
    region: str,
    tariff_delta_pct: float,
    margin_threshold_pct: float = 15.0,
) -> dict:
    """Apply a tariff delta and flag MOs below margin threshold."""
    material_ids = await _materials_in_region(session, tenant_id, region)
    mos = await _mos_using_materials(session, tenant_id, material_ids)

    profile_result = await session.execute(
        select(LandedCostProfile).where(
            LandedCostProfile.tenant_id == tenant_id,
            LandedCostProfile.region == region,
        )
    )
    profile = profile_result.scalar_one_or_none()

    substitute_map = await _get_substitute_map(session, tenant_id)
    mos_below: list[dict] = []
    substitute_drafts: list[dict] = []
    affected_mo_ids: list[str] = []

    for mo in mos:
        margin_before = await compute_margin_adjusted_priority(session, tenant_id, mo)
        net_before = margin_before.net_margin_usd

        tariff_delta_usd = 0.0
        if profile:
            bom_line_result = await session.execute(
                select(BomLine)
                .join(BillOfMaterial, BomLine.bom_id == BillOfMaterial.id)
                .where(
                    BillOfMaterial.tenant_id == tenant_id,
                    BomLine.bom_id == mo.bom_id,
                    BomLine.component_id.in_(material_ids),
                )
            )
            for line in bom_line_result.scalars().all():
                tariff_delta_usd += _estimate_tariff_cost_delta(
                    profile,
                    float(mo.quantity or 1),
                    float(line.quantity_per or 1),
                    tariff_delta_pct,
                )

        net_after = net_before - tariff_delta_usd
        product_result = await session.execute(
            select(Product).where(Product.id == mo.product_id, Product.tenant_id == tenant_id)
        )
        product = product_result.scalar_one_or_none()
        unit_price = float(product.standard_cost or 0) * 1.35 if product else 0.0
        revenue = unit_price * float(mo.quantity or 1)
        margin_after_pct = (net_after / revenue * 100.0) if revenue > 0 else 0.0

        affected_mo_ids.append(str(mo.id))
        if margin_after_pct < margin_threshold_pct:
            mos_below.append(
                {
                    "mo_id": str(mo.id),
                    "net_margin_before": round(net_before, 2),
                    "net_margin_after": round(net_after, 2),
                    "erosion_usd": round(net_before - net_after, 2),
                }
            )
            for mat_id in material_ids:
                from_id = str(mat_id)
                to_id = substitute_map.get(from_id)
                if to_id:
                    substitute_drafts.append(
                        {
                            "mo_id": str(mo.id),
                            "from_material_id": from_id,
                            "to_material_id": to_id,
                            "status": "pending_approval",
                        }
                    )
                    break

    return {
        "affected_mo_count": len(mos),
        "affected_mo_ids": affected_mo_ids,
        "mos_below_threshold": mos_below,
        "substitute_drafts": substitute_drafts,
        "region": region,
        "tariff_delta_pct": tariff_delta_pct,
    }
