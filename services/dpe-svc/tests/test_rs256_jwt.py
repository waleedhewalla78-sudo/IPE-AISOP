"""RS256 JWT migration tests — Phase 0.1."""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
import pytest

from ipe_shared.auth.jwt import (
    AuthenticationError,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from ipe_shared.auth.jwt_keys import get_key_id, get_public_key_for_kid, use_rs256_signing


@pytest.fixture(autouse=True)
def rs256_env(monkeypatch):
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    priv = os.path.join(root, "config", "keys", "jwt-private.pem")
    pub = os.path.join(root, "config", "keys", "jwt-public.pem")
    if not os.path.exists(priv):
        pytest.skip("JWT keys not generated — run scripts/generate-jwt-keys.py")
    monkeypatch.setenv("JWT_SIGNING_MODE", "rs256")
    monkeypatch.setenv("JWT_PRIVATE_KEY_PATH", priv)
    monkeypatch.setenv("JWT_PUBLIC_KEY_PATH", pub)
    monkeypatch.setenv("JWT_KEY_ID", "ipe-rs256-v1")
    from ipe_shared.auth import jwt_keys

    jwt_keys.get_private_key_pem.cache_clear()
    jwt_keys.get_public_key_pem.cache_clear()


def test_signing_uses_rs256():
    assert use_rs256_signing() is True
    user_id = uuid4()
    tenant_id = uuid4()
    token = create_access_token(user_id, tenant_id, "planner")
    header = jwt.get_unverified_header(token)
    assert header["alg"] == "RS256"
    assert header["kid"] == get_key_id()


def test_verify_with_public_key():
    user_id = uuid4()
    tenant_id = uuid4()
    token = create_access_token(user_id, tenant_id, "admin")
    payload = decode_token(token)
    assert payload.sub == str(user_id)
    assert payload.role == "admin"
    assert payload.jti


def test_expired_token_raises():
    user_id = uuid4()
    tenant_id = uuid4()
    past = datetime.now(UTC) - timedelta(hours=1)
    payload = {
        "sub": str(user_id),
        "tenant_id": str(tenant_id),
        "role": "planner",
        "type": "access",
        "iat": past,
        "exp": past + timedelta(minutes=5),
        "jti": str(uuid4()),
    }
    from ipe_shared.auth.jwt_keys import get_private_key_pem

    token = jwt.encode(
        payload,
        get_private_key_pem(),
        algorithm="RS256",
        headers={"kid": get_key_id()},
    )
    with pytest.raises(AuthenticationError):
        decode_token(token)


def test_tampered_token_raises():
    token = create_access_token(uuid4(), uuid4(), "planner")
    parts = token.split(".")
    parts[1] = parts[1][:-2] + "XX"
    with pytest.raises(AuthenticationError):
        decode_token(".".join(parts))


def test_refresh_token_flow():
    user_id = uuid4()
    tenant_id = uuid4()
    refresh = create_refresh_token(user_id, tenant_id, "planner")
    payload = decode_token(refresh)
    assert payload.type == "refresh"


def test_trusted_key_lookup():
    kid = get_key_id()
    key = get_public_key_for_kid(kid)
    assert "PUBLIC KEY" in key
