"""Stripe billing API tests — R2-03."""

import pytest


@pytest.mark.asyncio
async def test_stripe_plans(client):
    response = await client.get("/api/v1/billing/stripe/plans")
    assert response.status_code == 200
    assert "plans" in response.json()


@pytest.mark.asyncio
async def test_stripe_customer_and_subscription_flow(client):
    create = await client.post(
        "/api/v1/billing/stripe/customers",
        json={"email": "billing@demo.com", "name": "Demo Co", "tenant_id": "t1"},
    )
    assert create.status_code == 200
    customer_id = create.json()["customer_id"]

    sub = await client.post(
        "/api/v1/billing/stripe/subscriptions",
        json={"customer_id": customer_id, "plan": "professional_monthly_15000"},
    )
    assert sub.status_code == 200
    sub_id = sub.json()["subscription_id"]

    get_sub = await client.get(f"/api/v1/billing/stripe/subscriptions/{sub_id}")
    assert get_sub.status_code == 200
    assert get_sub.json()["plan"] == "professional_monthly_15000"

    cancel = await client.post(f"/api/v1/billing/stripe/subscriptions/{sub_id}/cancel")
    assert cancel.status_code == 200
    assert cancel.json()["cancel_at_period_end"] is True

    invoices = await client.get(f"/api/v1/billing/stripe/invoices/{customer_id}")
    assert invoices.status_code == 200
    assert "invoices" in invoices.json()


@pytest.mark.asyncio
async def test_stripe_subscription_not_found(client):
    response = await client.get("/api/v1/billing/stripe/subscriptions/missing-id")
    assert response.status_code == 200
    assert response.json()["error"] == "Subscription not found"
