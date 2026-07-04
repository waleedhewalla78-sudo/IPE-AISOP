"""Unit tests for tenant-scoped Kafka consumer groups."""

from ipe_shared.events.consumer import get_consumer_group, resolve_consumer_tenant_id


def test_get_consumer_group_formats_tenant_and_base():
    tenant = "aaaaaaaa-1111-4111-8111-111111111111"
    assert get_consumer_group("fea-svc", tenant) == f"ipe.{tenant}.fea-svc"
    assert get_consumer_group("feasibility", tenant) == f"ipe.{tenant}.feasibility"


def test_get_consumer_group_sanitizes_invalid_chars():
    group = get_consumer_group("feasibility", "tenant/with spaces")
    assert group == "ipe.tenant-with-spaces.feasibility"


def test_resolve_consumer_tenant_id_prefers_explicit(monkeypatch):
    monkeypatch.delenv("IPE_KAFKA_CONSUMER_TENANT_ID", raising=False)
    assert resolve_consumer_tenant_id("explicit-tenant") == "explicit-tenant"


def test_resolve_consumer_tenant_id_from_env(monkeypatch):
    monkeypatch.setenv("IPE_KAFKA_CONSUMER_TENANT_ID", "env-tenant")
    assert resolve_consumer_tenant_id() == "env-tenant"
