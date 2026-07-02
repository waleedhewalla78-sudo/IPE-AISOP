"""Unit tests for Vault secret loader."""

import os
from unittest.mock import MagicMock, patch

import pytest

from ipe_shared.vault_loader import (
    clear_vault_cache,
    get_vault_secret,
    resolve_secret,
    vault_enabled,
)


@pytest.fixture(autouse=True)
def _clear_cache():
    clear_vault_cache()
    yield
    clear_vault_cache()


def test_vault_disabled_by_default(monkeypatch):
    monkeypatch.delenv("VAULT_ENABLED", raising=False)
    assert vault_enabled() is False
    assert resolve_secret("MISSING_KEY", default="fallback") == "fallback"


def test_resolve_secret_env_first(monkeypatch):
    monkeypatch.setenv("IPE_DATABASE_PASSWORD", "from-env")
    assert resolve_secret("IPE_DATABASE_PASSWORD") == "from-env"


def test_get_vault_secret_mocked(monkeypatch):
    monkeypatch.setenv("VAULT_ENABLED", "true")
    monkeypatch.setenv("VAULT_TOKEN", "test-token")
    mock_client = MagicMock()
    mock_client.is_authenticated.return_value = True
    mock_client.secrets.kv.v2.read_secret_version.return_value = {
        "data": {"data": {"password": "vault-pass"}}
    }
    with patch("ipe_shared.vault_loader._hvac_client", return_value=mock_client):
        assert get_vault_secret("database", "password") == "vault-pass"
