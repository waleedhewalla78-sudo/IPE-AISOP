import os
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from ipe_shared.auth.dependencies import get_current_user
from ipe_shared.auth.jwt import create_access_token, decode_token
from ipe_shared.auth.keycloak import KeycloakTokenValidator, auth_provider, keycloak_token_to_payload


def test_auth_provider_defaults_local():
    os.environ.pop("AUTH_PROVIDER", None)
    assert auth_provider() == "local"


def test_local_jwt_roundtrip():
    token = create_access_token(uuid4(), uuid4(), "planner")
    payload = decode_token(token)
    assert payload.role == "planner"


def test_keycloak_role_mapping():
    validator = KeycloakTokenValidator(config=MagicMock())
    role = validator.map_roles({"realm_access": {"roles": ["ipe-planner", "other"]}})
    assert role == "planner"


def test_keycloak_token_to_payload_mocked():
    with patch.object(KeycloakTokenValidator, "validate", return_value={
        "sub": "user-1",
        "tenant_id": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
        "realm_access": {"roles": ["ipe-admin"]},
    }):
        os.environ["AUTH_PROVIDER"] = "keycloak"
        payload = keycloak_token_to_payload("fake-token")
        assert payload.role == "admin"
        os.environ["AUTH_PROVIDER"] = "local"
