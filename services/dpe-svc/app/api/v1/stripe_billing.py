"""Stripe billing API endpoints for demo."""
from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from ipe_shared.billing.stripe_mock import get_stripe_service, StripePlan

router = APIRouter(prefix="/billing/stripe", tags=["billing"])


class CreateCustomerRequest(BaseModel):
    email: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    tenant_id: str = Field(..., min_length=1)


class CreateSubscriptionRequest(BaseModel):
    customer_id: str = Field(..., min_length=1)
    plan: StripePlan


@router.get("/plans")
async def list_plans() -> dict:
    service = get_stripe_service()
    return {"plans": service.get_plan_pricing()}


@router.post("/customers")
async def create_customer(body: CreateCustomerRequest) -> dict:
    service = get_stripe_service()
    customer = service.create_customer(body.email, body.name, body.tenant_id)
    return {"customer_id": customer.customer_id, "email": customer.email, "name": customer.name}


@router.post("/subscriptions")
async def create_subscription(body: CreateSubscriptionRequest) -> dict:
    service = get_stripe_service()
    sub = service.create_subscription(body.customer_id, body.plan)
    return {
        "subscription_id": sub.subscription_id,
        "plan": sub.plan.value,
        "status": sub.status.value,
        "current_period_end": sub.current_period_end,
    }


@router.get("/subscriptions/{subscription_id}")
async def get_subscription(subscription_id: str) -> dict:
    service = get_stripe_service()
    sub = service.get_subscription(subscription_id)
    if not sub:
        return {"error": "Subscription not found"}
    return {
        "subscription_id": sub.subscription_id,
        "plan": sub.plan.value,
        "status": sub.status.value,
    }


@router.post("/subscriptions/{subscription_id}/cancel")
async def cancel_subscription(subscription_id: str) -> dict:
    service = get_stripe_service()
    sub = service.cancel_subscription(subscription_id)
    if not sub:
        return {"error": "Subscription not found"}
    return {"subscription_id": sub.subscription_id, "status": sub.status.value, "cancel_at_period_end": sub.cancel_at_period_end}


@router.get("/invoices/{customer_id}")
async def list_invoices(customer_id: str) -> dict:
    service = get_stripe_service()
    invoices = service.get_invoices(customer_id)
    return {"invoices": [{"id": i.invoice_id, "amount": i.amount_cents / 100, "status": i.status} for i in invoices]}
