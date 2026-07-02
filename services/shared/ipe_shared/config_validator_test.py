"""Tests for ipe_shared.config_validator."""

from __future__ import annotations

import pytest

from ipe_shared.config_validator import (
    ConfigReport,
    VarReport,
    VarStatus,
    validate_config,
)


def _set_base_env(monkeypatch, *, hs256: bool = True) -> None:
    monkeypatch.setenv("IPE_DATABASE_URL", "postgresql+asyncpg://user:pass@host/db")
    monkeypatch.setenv("IPE_REDIS_URL", "redis://redis:6379/0")
    if hs256:
        monkeypatch.setenv("IPE_JWT_SIGNING_MODE", "hs256")
    else:
        monkeypatch.delenv("IPE_JWT_SIGNING_MODE", raising=False)
        monkeypatch.setenv("IPE_JWT_PUBLIC_KEY_PATH", "/app/config/keys/jwt-public.pem")


class TestVarStatus:
    def test_ok_value(self):
        assert VarStatus.OK.value == "ok"

    def test_missing_value(self):
        assert VarStatus.MISSING.value == "missing"

    def test_placeholder_value(self):
        assert VarStatus.PLACEHOLDER.value == "placeholder"


class TestVarReport:
    def test_basic_creation(self):
        report = VarReport(name="FOO", status=VarStatus.OK, value_preview="bar")
        assert report.name == "FOO"
        assert report.status == VarStatus.OK
        assert report.message == ""

    def test_with_message(self):
        report = VarReport(
            name="BAZ", status=VarStatus.MISSING, value_preview="", message="Not set"
        )
        assert report.message == "Not set"


class TestConfigReport:
    def test_empty_report_all_ok(self):
        report = ConfigReport()
        assert report.all_ok is True
        assert report.missing_required == []
        assert report.placeholders == []

    def test_missing_required_detected(self):
        report = ConfigReport()
        report.required.append(VarReport(
            name="DATABASE_URL", status=VarStatus.MISSING, value_preview="",
        ))
        assert len(report.missing_required) == 1
        assert report.missing_required[0].name == "DATABASE_URL"

    def test_placeholders_detected(self):
        report = ConfigReport()
        report.required.append(VarReport(
            name="JWT_SECRET_KEY", status=VarStatus.PLACEHOLDER,
            value_preview="sk-ant-placeholder...",
        ))
        assert len(report.placeholders) == 1

    def test_summary_contains_all_sections(self):
        report = ConfigReport()
        report.required.append(VarReport(
            name="DATABASE_URL", status=VarStatus.OK, value_preview="postgresql://...",
        ))
        report.optional.append(VarReport(
            name="SENTRY_DSN", status=VarStatus.OK, value_preview="",
            message="Not set — using default: ",
        ))
        summary = report.summary()
        assert "REQUIRED" in summary
        assert "OPTIONAL" in summary
        assert "DATABASE_URL" in summary
        assert "SENTRY_DSN" in summary


class TestValidateConfig:
    def test_all_required_set_no_placeholders(self, monkeypatch):
        _set_base_env(monkeypatch)
        report = validate_config()
        assert report.all_ok is True
        assert report.missing_required == []
        assert len(report.required) == 2

    def test_missing_required_raises(self, monkeypatch):
        _set_base_env(monkeypatch)
        monkeypatch.delenv("IPE_DATABASE_URL", raising=False)
        monkeypatch.delenv("DATABASE_URL", raising=False)
        match = r"Missing required environment variables.*DATABASE_URL"
        with pytest.raises(ValueError, match=match):
            validate_config()

    def test_rs256_requires_public_key(self, monkeypatch):
        _set_base_env(monkeypatch, hs256=False)
        monkeypatch.delenv("IPE_JWT_PUBLIC_KEY_PATH", raising=False)
        monkeypatch.delenv("JWT_PUBLIC_KEY_PATH", raising=False)
        with pytest.raises(ValueError, match="JWT_PUBLIC_KEY_PATH"):
            validate_config()

    def test_optional_uses_defaults_when_unset(self, monkeypatch):
        _set_base_env(monkeypatch)
        monkeypatch.delenv("IPE_SENTRY_DSN", raising=False)
        report = validate_config()
        sentry = next(r for r in report.optional if r.name == "SENTRY_DSN")
        assert sentry.status == VarStatus.OK
        assert "default" in sentry.message

    def test_sk_ant_placeholder_detected(self, monkeypatch):
        _set_base_env(monkeypatch)
        monkeypatch.setenv("IPE_ANTHROPIC_API_KEY", "sk-ant-placeholder")
        report = validate_config()
        anthropic = next(r for r in report.optional if r.name == "ANTHROPIC_API_KEY")
        assert anthropic.status == VarStatus.PLACEHOLDER

    def test_unprefixed_keys_also_read(self, monkeypatch):
        monkeypatch.delenv("IPE_DATABASE_URL", raising=False)
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@host/db")
        _set_base_env(monkeypatch)
        report = validate_config()
        db = next(r for r in report.required if r.name == "DATABASE_URL")
        assert db.status == VarStatus.OK
