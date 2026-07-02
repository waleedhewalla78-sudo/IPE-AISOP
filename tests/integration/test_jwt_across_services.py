"""Cross-service RS256 JWT acceptance (integration smoke)."""

from __future__ import annotations

import os
from uuid import uuid4

import pytest

from ipe_shared.auth.jwt import create_access_token, decode_token
from ipe_shared.auth.jwt_verify import verify_service_token


@pytest.fixture(autouse=True)
def rs256_keys(monkeypatch):
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    priv = os.path.join(root, "config", "keys", "jwt-private.pem")
    pub = os.path.join(root, "config", "keys", "jwt-public.pem")
    if not os.path.exists(priv):
        pytest.skip("JWT keys missing")
    monkeypatch.setenv("IPE_JWT_SIGNING_MODE", "rs256")
    monkeypatch.setenv("IPE_JWT_PRIVATE_KEY_PATH", priv)
    monkeypatch.setenv("IPE_JWT_PUBLIC_KEY_PATH", pub)
    from ipe_shared.auth import jwt_keys

    jwt_keys.get_private_key_pem.cache_clear()
    jwt_keys.get_public_key_pem.cache_clear()


def test_rs256_token_verified_by_shared_verifier():
    user_id = uuid4()
    tenant_id = uuid4()
    token = create_access_token(user_id, tenant_id, "planner")
    payload = verify_service_token(token)
    assert payload["sub"] == str(user_id)
    assert payload["tenant_id"] == str(tenant_id)


def test_decode_token_matches_verifier():
    user_id = uuid4()
    tenant_id = uuid4()
    token = create_access_token(user_id, tenant_id, "admin")
    model = decode_token(token)
    raw = verify_service_token(token)
    assert model.sub == raw["sub"]
    assert model.tenant_id == raw["tenant_id"]
