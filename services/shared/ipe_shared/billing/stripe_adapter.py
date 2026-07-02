"""
Stripe billing adapter — currently mock, POST-B activation required.

Activation steps:
1. Set STRIPE_SECRET_KEY and STRIPE_WEBHOOK_SECRET
2. Set BILLING_PROVIDER=stripe
3. Configure Stripe webhook endpoint for billing events

Mapped events:
- customer.subscription.created → provision tenant
- customer.subscription.updated → adjust tenant limits
- invoice.payment_failed → alert + grace period
- customer.subscription.deleted → deprovision tenant
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from typing import Any
from uuid import uuid4

from ipe_shared.billing.stripe_mock import StripeMockService, StripePlan


class BillingProvider(ABC):
    @abstractmethod
    async def create_subscription(self, tenant_id: str, plan_id: str) -> dict[str, Any]:
        ...

    @abstractmethod
    async def cancel_subscription(self, subscription_id: str) -> dict[str, Any]:
        ...

    @abstractmethod
    async def get_usage(self, tenant_id: str, period: str) -> dict[str, Any]:
        ...

    @abstractmethod
    async def webhook_handler(self, event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        ...


class MockBillingProvider(BillingProvider):
    def __init__(self) -> None:
        self._mock = StripeMockService()

    async def create_subscription(self, tenant_id: str, plan_id: str) -> dict[str, Any]:
        customer = self._mock.create_customer(email=f"{tenant_id}@ipe.local", name=tenant_id, tenant_id=tenant_id)
        plan = StripePlan(plan_id) if plan_id in StripePlan._value2member_map_ else StripePlan.BASIC
        sub = self._mock.create_subscription(customer.customer_id, plan)
        return {"subscription_id": sub.subscription_id, "status": sub.status}

    async def cancel_subscription(self, subscription_id: str) -> dict[str, Any]:
        return self._mock.cancel_subscription(subscription_id)

    async def get_usage(self, tenant_id: str, period: str) -> dict[str, Any]:
        return {"tenant_id": tenant_id, "period": period, "api_calls": 0, "compute_minutes": 0}

    async def webhook_handler(self, event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        return {"handled": True, "event_type": event_type, "action": "mock_noop"}


class StripeBillingProvider(BillingProvider):
    """POST-B scaffold — wire stripe Python SDK."""

    async def create_subscription(self, tenant_id: str, plan_id: str) -> dict[str, Any]:
        raise NotImplementedError("Set STRIPE_SECRET_KEY and BILLING_PROVIDER=stripe (POST-B)")

    async def cancel_subscription(self, subscription_id: str) -> dict[str, Any]:
        raise NotImplementedError("Stripe activation required (POST-B)")

    async def get_usage(self, tenant_id: str, period: str) -> dict[str, Any]:
        raise NotImplementedError("Stripe activation required (POST-B)")

    async def webhook_handler(self, event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        handlers = {
            "customer.subscription.created": "provision_tenant",
            "customer.subscription.updated": "adjust_tenant_limits",
            "invoice.payment_failed": "alert_grace_period",
            "customer.subscription.deleted": "deprovision_tenant",
        }
        return {"handled": False, "event_type": event_type, "planned_action": handlers.get(event_type, "unknown")}


def get_billing_provider() -> BillingProvider:
    if os.getenv("BILLING_PROVIDER", "mock").lower() == "stripe":
        return StripeBillingProvider()
    return MockBillingProvider()
