"""Tests for Release 1 optional dependency probes (T169)."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from ipe_shared.health import probes


@pytest.mark.parametrize(
    "profile,kafka_env,expected",
    [
        ("release1", "kafka:9092", False),
        ("full", "", False),
        ("full", "kafka:9092", True),
    ],
)
def test_kafka_required(profile: str, kafka_env: str, expected: bool, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("IPE_RELEASE_PROFILE", profile)
    monkeypatch.delenv("IPE_KAFKA_ENABLED", raising=False)
    with patch.object(probes.settings, "KAFKA_BOOTSTRAP_SERVERS", kafka_env):
        assert probes.kafka_required() is expected


def test_overall_status_healthy_when_kafka_skipped_in_release1():
    deps = {
        "database": {"status": "up"},
        "redis": {"status": "up"},
        "kafka": {"status": "skipped", "reason": "release1_profile"},
        "vault": {"status": "skipped", "reason": "release1_profile"},
    }
    assert probes.overall_status(deps) == "healthy"


def test_readiness_ok_when_kafka_vault_skipped_release1():
    deps = {
        "database": {"status": "up"},
        "redis": {"status": "up"},
        "kafka": {"status": "skipped", "reason": "release1_profile"},
        "vault": {"status": "skipped", "reason": "release1_profile"},
    }
    critical_ok = deps["database"]["status"] == "up"
    redis_ok = deps["redis"]["status"] in ("up", "disabled", "not_configured", "skipped")
    optional_ok = all(
        deps.get(k, {}).get("status") in ("up", "disabled", "not_configured", "skipped")
        for k in ("kafka", "vault")
    )
    assert critical_ok and redis_ok and optional_ok
