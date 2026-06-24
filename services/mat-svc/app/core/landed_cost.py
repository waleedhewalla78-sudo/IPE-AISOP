"""Total Landed Cost (TLC) computation from DB profiles."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ipe_shared.models.landed_cost import LandedCostProfile
from ipe_shared.models.material_attributes import MaterialAttribute


def _profile_to_breakdown(
    profile: LandedCostProfile,
    *,
    tariff_delta_pct: float = 0.0,
) -> dict:
    base = float(profile.base_cost_usd or 0)
    freight = float(profile.freight_usd or 0)
    tariff_pct = float(profile.tariff_pct or 0) + tariff_delta_pct
    risk_pct = float(profile.risk_premium_pct or 0)
    tariff_usd = base * tariff_pct / 100.0
    risk_usd = base * risk_pct / 100.0
    total = base + freight + tariff_usd + risk_usd
    return {
        "landed_cost_per_unit": round(total, 4),
        "landed_cost_breakdown": {
            "base_usd": round(base, 4),
            "freight_usd": round(freight, 4),
            "tariff_usd": round(tariff_usd, 4),
            "risk_premium_usd": round(risk_usd, 4),
        },
    }


async def _load_material_attributes(
    session: AsyncSession,
    tenant_id: UUID,
    material_id: UUID,
) -> dict | None:
    result = await session.execute(
        select(MaterialAttribute).where(
            MaterialAttribute.tenant_id == tenant_id,
            MaterialAttribute.material_id == material_id,
        )
    )
    row = result.scalar_one_or_none()
    return dict(row.attributes) if row and row.attributes else None


async def _load_landed_cost_profile(
    session: AsyncSession,
    tenant_id: UUID,
    region: str,
) -> LandedCostProfile | None:
    result = await session.execute(
        select(LandedCostProfile).where(
            LandedCostProfile.tenant_id == tenant_id,
            LandedCostProfile.region == region,
        )
    )
    return result.scalar_one_or_none()


async def compute_landed_cost(
    session: AsyncSession,
    tenant_id: UUID,
    material_id: UUID,
    *,
    region: str | None = None,
    tariff_delta_pct: float = 0.0,
) -> dict:
    """Compute TLC for a material using attributes + regional profile."""
    attrs = await _load_material_attributes(session, tenant_id, material_id)
    resolved_region = region or (attrs or {}).get("origin_region")
    material_attributes = attrs or {}

    if not resolved_region:
        return {
            "landed_cost_per_unit": 0.0,
            "landed_cost_breakdown": {
                "base_usd": 0.0,
                "freight_usd": 0.0,
                "tariff_usd": 0.0,
                "risk_premium_usd": 0.0,
            },
            "material_attributes": material_attributes,
        }

    profile = await _load_landed_cost_profile(session, tenant_id, resolved_region)
    if not profile:
        return {
            "landed_cost_per_unit": 0.0,
            "landed_cost_breakdown": {
                "base_usd": 0.0,
                "freight_usd": 0.0,
                "tariff_usd": 0.0,
                "risk_premium_usd": 0.0,
            },
            "material_attributes": material_attributes,
        }

    breakdown = _profile_to_breakdown(profile, tariff_delta_pct=tariff_delta_pct)
    breakdown["material_attributes"] = material_attributes
    return breakdown
