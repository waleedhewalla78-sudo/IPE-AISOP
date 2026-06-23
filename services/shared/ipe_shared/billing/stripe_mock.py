"""Stripe billing mock for IPE demo.

Provides a working Stripe-like billing API with:
- Customer management
- Subscription management (Basic/Professional/Enterprise)
- Invoice generation
- Payment intent simulation
- Usage record tracking
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4

logger = logging.getLogger("ipe.billing.stripe")


class StripeSubscriptionStatus(StrEnum):
    ACTIVE = "active"
    PAST_DUE = "past_due"
    UNPAID = "unpaid"
    CANCELED = "canceled"
    TRIALING = "trialing"
    INCOMPLETE = "incomplete"
    INCOMPLETE_EXPIRED = "incomplete_expired"


class StripePlan(StrEnum):
    BASIC = "basic_monthly_5000"
    PROFESSIONAL = "professional_monthly_15000"
    ENTERPRISE = "enterprise_monthly_50000"


@dataclass
class StripeCustomer:
    customer_id: str
    email: str
    name: str
    tenant_id: str
    created_at: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.created_at:
            self.created_at = datetime.now(UTC).isoformat()


@dataclass
class StripeSubscription:
    subscription_id: str
    customer_id: str
    plan: StripePlan
    status: StripeSubscriptionStatus
    current_period_start: str = ""
    current_period_end: str = ""
    cancel_at_period_end: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        now = datetime.now(UTC)
        if not self.current_period_start:
            self.current_period_start = now.replace(day=1).isoformat()
        if not self.current_period_end:
            if now.month == 12:
                end = now.replace(year=now.year + 1, month=1)
            else:
                end = now.replace(month=now.month + 1)
            self.current_period_end = end.isoformat()


@dataclass
class StripeInvoice:
    invoice_id: str
    customer_id: str
    subscription_id: str
    amount_cents: int
    status: str = "paid"
    period_start: str = ""
    period_end: str = ""
    lines: list[dict[str, Any]] = field(default_factory=list)
    created_at: str = ""

    def __post_init__(self) -> None:
        if not self.created_at:
            self.created_at = datetime.now(UTC).isoformat()


@dataclass
class StripePaymentIntent:
    payment_intent_id: str
    customer_id: str
    amount_cents: int
    currency: str = "usd"
    status: str = "succeeded"
    created_at: str = ""

    def __post_init__(self) -> None:
        if not self.created_at:
            self.created_at = datetime.now(UTC).isoformat()


PLAN_PRICES: dict[StripePlan, dict[str, Any]] = {
    StripePlan.BASIC: {"amount_cents": 500000, "name": "Basic", "features": ["scheduling", "basic_analytics"]},
    StripePlan.PROFESSIONAL: {"amount_cents": 1500000, "name": "Professional", "features": ["scheduling", "advanced_analytics", "digital_twin", "sso"]},
    StripePlan.ENTERPRISE: {"amount_cents": 5000000, "name": "Enterprise", "features": ["all_features", "priority_support", "custom_integrations"]},
}


class StripeMockService:
    """Mock Stripe service for demo without real Stripe account."""

    def __init__(self) -> None:
        self._customers: dict[str, StripeCustomer] = {}
        self._subscriptions: dict[str, StripeSubscription] = {}
        self._invoices: list[StripeInvoice] = []
        self._payment_intents: list[StripePaymentIntent] = []
        self._setup_demo_data()

    def _setup_demo_data(self) -> None:
        demo_customer = StripeCustomer(
            customer_id="cus_demo_ipe_001",
            email="billing@ipe.ai",
            name="IPE Demo Customer",
            tenant_id="a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
        )
        self._customers[demo_customer.customer_id] = demo_customer

        demo_sub = StripeSubscription(
            subscription_id="sub_demo_ipe_001",
            customer_id="cus_demo_ipe_001",
            plan=StripePlan.PROFESSIONAL,
            status=StripeSubscriptionStatus.ACTIVE,
        )
        self._subscriptions[demo_sub.subscription_id] = demo_sub

    def create_customer(self, email: str, name: str, tenant_id: str) -> StripeCustomer:
        customer = StripeCustomer(
            customer_id=f"cus_{uuid4().hex[:14]}",
            email=email,
            name=name,
            tenant_id=tenant_id,
        )
        self._customers[customer.customer_id] = customer
        logger.info("Stripe customer created: %s (%s)", customer.customer_id, email)
        return customer

    def create_subscription(self, customer_id: str, plan: StripePlan) -> StripeSubscription:
        if customer_id not in self._customers:
            raise ValueError(f"Customer not found: {customer_id}")

        subscription = StripeSubscription(
            subscription_id=f"sub_{uuid4().hex[:14]}",
            customer_id=customer_id,
            plan=plan,
            status=StripeSubscriptionStatus.ACTIVE,
        )
        self._subscriptions[subscription.subscription_id] = subscription
        logger.info("Stripe subscription created: %s (%s)", subscription.subscription_id, plan.value)
        return subscription

    def get_subscription(self, subscription_id: str) -> StripeSubscription | None:
        return self._subscriptions.get(subscription_id)

    def cancel_subscription(self, subscription_id: str) -> StripeSubscription | None:
        sub = self._subscriptions.get(subscription_id)
        if sub:
            sub.status = StripeSubscriptionStatus.CANCELED
            sub.cancel_at_period_end = True
            logger.info("Stripe subscription canceled: %s", subscription_id)
        return sub

    def create_invoice(self, customer_id: str, subscription_id: str, amount_cents: int) -> StripeInvoice:
        invoice = StripeInvoice(
            invoice_id=f"in_{uuid4().hex[:14]}",
            customer_id=customer_id,
            subscription_id=subscription_id,
            amount_cents=amount_cents,
            lines=[{"amount": amount_cents, "description": "IPE Subscription"}],
        )
        self._invoices.append(invoice)
        logger.info("Stripe invoice created: %s (%d cents)", invoice.invoice_id, amount_cents)
        return invoice

    def get_invoices(self, customer_id: str) -> list[StripeInvoice]:
        return [i for i in self._invoices if i.customer_id == customer_id]

    def create_payment_intent(self, customer_id: str, amount_cents: int) -> StripePaymentIntent:
        pi = StripePaymentIntent(
            payment_intent_id=f"pi_{uuid4().hex[:14]}",
            customer_id=customer_id,
            amount_cents=amount_cents,
        )
        self._payment_intents.append(pi)
        logger.info("Stripe payment intent created: %s (%d cents)", pi.payment_intent_id, amount_cents)
        return pi

    def get_plan_pricing(self) -> dict[str, Any]:
        return {
            plan.value: {
                "name": info["name"],
                "amount_monthly": info["amount_cents"] / 100,
                "features": info["features"],
            }
            for plan, info in PLAN_PRICES.items()
        }


_stripe_service: StripeMockService | None = None


def get_stripe_service() -> StripeMockService:
    global _stripe_service
    if _stripe_service is None:
        _stripe_service = StripeMockService()
    return _stripe_service
