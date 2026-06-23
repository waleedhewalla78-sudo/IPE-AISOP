"""Tiered pricing API endpoints for IPE SaaS billing."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from ipe_shared.billing.pricing import PricingService, PricingTier, TIER_CONFIGS

router = APIRouter(prefix="/billing", tags=["billing"])


class TierInfo(BaseModel):
    tier: str
    monthly_price: float
    included_api_calls: int
    included_user_seats: int
    included_storage_gb: int
    included_compute_minutes: int
    features: list[str]


class PricingOverview(BaseModel):
    tiers: list[TierInfo]


_pricing_service = PricingService()


@router.get("/pricing", response_model=PricingOverview)
async def get_pricing_overview() -> PricingOverview:
    """Get pricing overview for all tiers."""
    tiers = []
    for tier in PricingTier:
        config = TIER_CONFIGS[tier]
        tiers.append(TierInfo(
            tier=tier.value,
            monthly_price=config.monthly_base_price_cents / 100.0,
            included_api_calls=config.included_api_calls,
            included_user_seats=config.included_user_seats,
            included_storage_gb=config.included_storage_gb,
            included_compute_minutes=config.included_compute_minutes,
            features=config.features,
        ))
    return PricingOverview(tiers=tiers)


@router.get("/pricing/{tier}")
async def get_tier_details(tier: PricingTier) -> TierInfo:
    """Get detailed pricing for a specific tier."""
    config = TIER_CONFIGS[tier]
    return TierInfo(
        tier=tier.value,
        monthly_price=config.monthly_base_price_cents / 100.0,
        included_api_calls=config.included_api_calls,
        included_user_seats=config.included_user_seats,
        included_storage_gb=config.included_storage_gb,
        included_compute_minutes=config.included_compute_minutes,
        features=config.features,
    )


class InvoiceRequest(BaseModel):
    tenant_id: str = Field(..., min_length=1)
    tier: PricingTier
    usage: dict[str, int] = Field(default_factory=dict)


class InvoiceResponse(BaseModel):
    tenant_id: str
    tier: str
    base_cost: float
    overage_cost: float
    total_cost: float
    period_start: str
    period_end: str


@router.post("/invoice", response_model=InvoiceResponse)
async def calculate_invoice(body: InvoiceRequest) -> InvoiceResponse:
    """Calculate monthly invoice for a tenant."""
    period = _pricing_service.calculate_invoice(
        tenant_id=body.tenant_id,
        tier=body.tier,
        usage=body.usage,
    )
    return InvoiceResponse(
        tenant_id=period.tenant_id,
        tier=period.tier.value,
        base_cost=period.base_cost_cents / 100.0,
        overage_cost=period.overage_cost_cents / 100.0,
        total_cost=period.total_cost_dollars,
        period_start=period.period_start,
        period_end=period.period_end,
    )
