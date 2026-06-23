"""Tiered pricing enforcement for IPE SaaS.

Three tiers: BASIC ($5K), PROFESSIONAL ($15K), ENTERPRISE ($50K).
Usage metering for API calls, user seats, storage, and compute minutes.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum

logger = logging.getLogger("ipe.billing.pricing")


class PricingTier(StrEnum):
    BASIC = "basic"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class MeteredResource(StrEnum):
    API_CALLS = "api_calls"
    USER_SEATS = "user_seats"
    STORAGE_GB = "storage_gb"
    COMPUTE_MINUTES = "compute_minutes"


@dataclass
class TierConfig:
    tier: PricingTier
    monthly_base_price_cents: int
    included_api_calls: int
    included_user_seats: int
    included_storage_gb: int
    included_compute_minutes: int
    overage_api_call_cents: int = 0
    overage_user_seat_cents: int = 0
    overage_storage_gb_cents: int = 0
    overage_compute_minute_cents: int = 0
    features: list[str] = field(default_factory=list)


TIER_CONFIGS: dict[PricingTier, TierConfig] = {
    PricingTier.BASIC: TierConfig(
        tier=PricingTier.BASIC,
        monthly_base_price_cents=500000,
        included_api_calls=100_000,
        included_user_seats=5,
        included_storage_gb=50,
        included_compute_minutes=10_000,
        overage_api_call_cents=1,
        overage_user_seat_cents=500,
        overage_storage_gb_cents=100,
        overage_compute_minute_cents=10,
        features=["scheduling", "basic_analytics", "email_support"],
    ),
    PricingTier.PROFESSIONAL: TierConfig(
        tier=PricingTier.PROFESSIONAL,
        monthly_base_price_cents=1500000,
        included_api_calls=500_000,
        included_user_seats=25,
        included_storage_gb=500,
        included_compute_minutes=50_000,
        overage_api_call_cents=0.5,
        overage_user_seat_cents=400,
        overage_storage_gb_cents=80,
        overage_compute_minute_cents=8,
        features=["scheduling", "advanced_analytics", "digital_twin", "priority_support", "sso"],
    ),
    PricingTier.ENTERPRISE: TierConfig(
        tier=PricingTier.ENTERPRISE,
        monthly_base_price_cents=5000000,
        included_api_calls=2_000_000,
        included_user_seats=100,
        included_storage_gb=2_000,
        included_compute_minutes=200_000,
        overage_api_call_cents=0.25,
        overage_user_seat_cents=300,
        overage_storage_gb_cents=50,
        overage_compute_minute_cents=5,
        features=[
            "scheduling", "advanced_analytics", "digital_twin", "xai",
            "progressive_autonomy", "priority_support", "sso", "byok",
            "custom_integrations", "dedicated_support",
        ],
    ),
}


@dataclass
class UsageRecord:
    resource: MeteredResource
    quantity: int
    recorded_at: str = ""

    def __post_init__(self) -> None:
        if not self.recorded_at:
            self.recorded_at = datetime.now(UTC).isoformat()


@dataclass
class BillingPeriod:
    tenant_id: str
    tier: PricingTier
    period_start: str
    period_end: str
    usage: dict[str, int] = field(default_factory=dict)
    base_cost_cents: int = 0
    overage_cost_cents: int = 0

    @property
    def total_cost_cents(self) -> int:
        return self.base_cost_cents + self.overage_cost_cents

    @property
    def total_cost_dollars(self) -> float:
        return self.total_cost_cents / 100.0


class PricingService:
    def __init__(self) -> None:
        self._periods: dict[str, BillingPeriod] = {}

    def get_tier_config(self, tier: PricingTier) -> TierConfig:
        return TIER_CONFIGS[tier]

    def calculate_overage(self, tier: PricingTier, usage: dict[str, int]) -> int:
        config = TIER_CONFIGS[tier]
        total_overage_cents = 0

        overage_map = {
            MeteredResource.API_CALLS.value: (config.included_api_calls, config.overage_api_call_cents),
            MeteredResource.USER_SEATS.value: (config.included_user_seats, config.overage_user_seat_cents),
            MeteredResource.STORAGE_GB.value: (config.included_storage_gb, config.overage_storage_gb_cents),
            MeteredResource.COMPUTE_MINUTES.value: (config.included_compute_minutes, config.overage_compute_minute_cents),
        }

        for resource, (included, per_unit_cents) in overage_map.items():
            used = usage.get(resource, 0)
            if used > included:
                overage = used - included
                total_overage_cents += overage * per_unit_cents
                logger.info("Overage: %s used %d, included %d, overage %d × %d¢ = %d¢",
                           resource, used, included, overage, per_unit_cents, overage * per_unit_cents)

        return total_overage_cents

    def calculate_invoice(self, tenant_id: str, tier: PricingTier, usage: dict[str, int]) -> BillingPeriod:
        config = TIER_CONFIGS[tier]
        now = datetime.now(UTC)
        period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if now.month == 12:
            period_end = period_start.replace(year=now.year + 1, month=1)
        else:
            period_end = period_start.replace(month=now.month + 1)

        overage = self.calculate_overage(tier, usage)
        period = BillingPeriod(
            tenant_id=tenant_id,
            tier=tier,
            period_start=period_start.isoformat(),
            period_end=period_end.isoformat(),
            usage=usage,
            base_cost_cents=config.monthly_base_price_cents,
            overage_cost_cents=overage,
        )

        self._periods[f"{tenant_id}:{period_start.isoformat()}"] = period
        logger.info("Invoice: tenant=%s tier=%s base=%d¢ overage=%d¢ total=%d¢",
                    tenant_id, tier.value, config.monthly_base_price_cents, overage, period.total_cost_cents)

        return period
