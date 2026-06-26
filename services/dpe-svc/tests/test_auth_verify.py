"""Auth password verification edge cases — R2-06."""

import hashlib

import pytest

from app.api.v1.auth import _verify_password


def test_verify_password_sha256_match():
    digest = hashlib.sha256(b"secret123").hexdigest()
    assert _verify_password("secret123", f"{{SHA-256}}{digest}") is True


def test_verify_password_sha256_mismatch():
    digest = hashlib.sha256(b"secret123").hexdigest()
    assert _verify_password("wrong", f"{{SHA-256}}{digest}") is False


def test_verify_password_dev_fallback(monkeypatch):
    monkeypatch.setattr("app.api.v1.auth.settings.ENVIRONMENT", "development")
    assert _verify_password("admin", None) is True
    assert _verify_password("admin", "$2b$hash") is True


def test_verify_password_production_rejects_dev(monkeypatch):
    monkeypatch.setattr("app.api.v1.auth.settings.ENVIRONMENT", "production")
    assert _verify_password("admin", None) is False
