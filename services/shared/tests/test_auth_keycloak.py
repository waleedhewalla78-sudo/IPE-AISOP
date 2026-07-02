import os
from unittest.mock import MagicMock, patch

import pytest

from ipe_shared.auth.keycloak import (
    KeycloakTokenValidator,
    auth_info,
    auth_provider,
    map_keycloak_roles,
    keycloak_token_to_payload,
)


def test_auth_provider_defaults_local(monkeypatch):
    monkeypatch.delenv("AUTH_PROVIDER", raising=False)
    monkeypatch.delenv("AUTH_MODE", raising=False)
    assert auth_provider() == "local"


def test_auth_provider_keycloak_env(monkeypatch):
    monkeypatch.setenv("AUTH_MODE", "keycloak")
    assert auth_provider() == "keycloak"


def test_keycloak_role_mapping():
    assert map_keycloak_roles({"realm_access": {"roles": ["ipe-planner", "other"]}}) == "planner"
    assert map_keycloak_roles({"realm_access": {"roles": ["admin"]}}) == "admin"
    assert map_keycloak_roles({"realm_access": {"roles": ["unknown"]}}) == "operator"


def test_keycloak_token_to_payload_mocked(monkeypatch):
    monkeypatch.setenv("KEYCLOAK_URL", "http://keycloak:8080")
    fake_key = MagicMock()
    fake_key.key = "secret"
    with patch("ipe_shared.auth.keycloak.get_keycloak_jwks_client") as mock_client:
        mock_client.return_value.get_signing_key_from_jwt.return_value = fake_key
        with patch("ipe_shared.auth.keycloak.jwt.decode", return_value={
            "sub": "user-1",
            "tenant_id": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
            "realm_access": {"roles": ["ipe-admin"]},
            "exp": 9999999999,
            "iat": 1,
        }):
            payload = keycloak_token_to_payload("fake-token")
            assert payload.role == "admin"
            assert payload.type == "access"


def test_auth_info_local(monkeypatch):
    monkeypatch.setenv("AUTH_MODE", "local")
    info = auth_info()
    assert info["mode"] == "local"
    assert info["keycloak_url"] == ""


def test_auth_info_keycloak_public_url(monkeypatch):
    monkeypatch.setenv("AUTH_MODE", "keycloak")
    monkeypatch.setenv("KEYCLOAK_URL", "http://keycloak:8080")
    monkeypatch.setenv("KEYCLOAK_PUBLIC_URL", "http://localhost:8180")
    info = auth_info()
    assert info["mode"] == "keycloak"
    assert info["keycloak_url"] == "http://localhost:8180"


def test_validator_backward_compat():
    validator = KeycloakTokenValidator()
    role = validator.map_roles({"realm_access": {"roles": ["planner"]}})
    assert role == "planner"
