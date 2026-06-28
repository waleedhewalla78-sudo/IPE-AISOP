import pytest

from ipe_shared.billing.stripe_adapter import MockBillingProvider, StripeBillingProvider, get_billing_provider


@pytest.mark.asyncio
async def test_mock_billing_create_subscription():
    provider = MockBillingProvider()
    result = await provider.create_subscription("tenant-1", "basic_monthly_5000")
    assert "subscription_id" in result


@pytest.mark.asyncio
async def test_stripe_billing_scaffold_raises():
    provider = StripeBillingProvider()
    with pytest.raises(NotImplementedError):
        await provider.create_subscription("tenant-1", "plan")


def test_get_billing_provider_mock_default():
    assert isinstance(get_billing_provider(), MockBillingProvider)
