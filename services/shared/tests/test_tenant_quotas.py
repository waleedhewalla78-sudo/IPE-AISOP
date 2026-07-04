"""Unit tests for tenant resource quotas."""

from pathlib import Path

import pytest
from fastapi import HTTPException

from ipe_shared.tenant.quotas import check_quota, enforce_quota, get_quota


@pytest.fixture
def quota_overrides(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    overrides = tmp_path / "tenant-quotas.json"
    overrides.write_text(
        '{"tenant-a": {"max_boms": 10, "max_products": 25}}',
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "ipe_shared.tenant.quotas.settings.TENANT_QUOTA_OVERRIDES",
        str(overrides),
    )
    return overrides


def test_get_quota_uses_defaults_when_no_override_file(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    missing = tmp_path / "missing.json"
    monkeypatch.setattr(
        "ipe_shared.tenant.quotas.settings.TENANT_QUOTA_OVERRIDES",
        str(missing),
    )
    quota = get_quota("unknown-tenant")
    assert quota.max_boms == 500
    assert quota.max_manufacturing_orders == 1000


def test_get_quota_applies_tenant_override(quota_overrides: Path):
    quota = get_quota("tenant-a")
    assert quota.max_boms == 10
    assert quota.max_products == 25
    assert quota.max_manufacturing_orders == 1000


@pytest.mark.asyncio
async def test_check_quota_allows_under_limit(quota_overrides: Path):
    assert await check_quota("tenant-a", "boms", 9) is True


@pytest.mark.asyncio
async def test_check_quota_blocks_at_limit(quota_overrides: Path):
    assert await check_quota("tenant-a", "boms", 10) is False


@pytest.mark.asyncio
async def test_check_quota_ignores_unknown_resource_type():
    assert await check_quota("tenant-a", "widgets", 9999) is True


@pytest.mark.asyncio
async def test_enforce_quota_raises_429(quota_overrides: Path):
    with pytest.raises(HTTPException) as exc:
        await enforce_quota("tenant-a", "boms", 10)
    assert exc.value.status_code == 429
    assert "boms quota" in exc.value.detail


@pytest.mark.asyncio
async def test_assert_quota_raises_quota_exceeded(quota_overrides: Path):
    from ipe_shared.tenant.quotas import QuotaExceededError, assert_quota

    with pytest.raises(QuotaExceededError):
        await assert_quota("tenant-a", "boms", 10)
