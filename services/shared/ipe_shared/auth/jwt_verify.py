"""Shared JWT verification for IPE microservices (RS256 + HS256 fallback)."""

from __future__ import annotations

import jwt

from ipe_shared.auth.jwt import decode_token
from ipe_shared.auth.jwt_keys import get_public_key_for_kid, use_rs256_signing
from ipe_shared.config import settings


def verify_service_token(token: str) -> dict:
    """Verify a JWT and return the raw payload dict."""
    if use_rs256_signing():
        header = jwt.get_unverified_header(token)
        kid = header.get("kid")
        public_key = get_public_key_for_kid(kid)
        return jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            options={"require": ["sub", "tenant_id", "exp", "iat"]},
        )
    return jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
        options={"require": ["sub", "tenant_id", "exp", "iat"]},
    )


def verify_service_token_model(token: str):
    """Verify token and return TokenPayload."""
    return decode_token(token)
