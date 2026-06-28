"""
Keycloak SSO integration scaffold — POST-B activation required.

Activation steps:
1. Set env vars: KEYCLOAK_URL, KEYCLOAK_REALM, KEYCLOAK_CLIENT_ID, KEYCLOAK_CLIENT_SECRET
2. Set AUTH_PROVIDER=keycloak in .env
3. Keycloak OIDC discovery: {KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}/.well-known/openid-configuration

This module provides:
- KeycloakTokenValidator: validates JWT tokens via JWKS endpoint
- keycloak_auth_dependency: FastAPI dependency that extracts user info from Keycloak token
- Role mapping: Keycloak realm roles → IPE RBAC roles
"""

from __future__ import annotations

import os
from typing import Any

from ipe_shared.auth.jwt import TokenPayload
from ipe_shared.auth.jwks import JWKSAuthBackend, JWKSConfig

KEYCLOAK_ROLE_MAP: dict[str, str] = {
    "ipe-admin": "admin",
    "ipe-planner": "planner",
    "ipe-manager": "manager",
    "ipe-executive": "executive",
    "ipe-operator": "operator",
    "ipe-auditor": "auditor",
}


def auth_provider() -> str:
    return os.getenv("AUTH_PROVIDER", "local").lower()


class KeycloakTokenValidator:
    """Validates Keycloak-issued JWTs via JWKS."""

    def __init__(self, config: JWKSConfig | None = None) -> None:
        self._config = config or JWKSConfig.from_settings()
        self._backend = JWKSAuthBackend(self._config)

    def validate(self, token: str) -> dict[str, Any]:
        if auth_provider() != "keycloak":
            raise RuntimeError("Keycloak validator called while AUTH_PROVIDER=local")
        return self._backend.validate_token(token)

    def map_roles(self, payload: dict[str, Any]) -> str:
        realm_access = payload.get("realm_access", {})
        roles = realm_access.get("roles", []) if isinstance(realm_access, dict) else []
        for role in roles:
            if role in KEYCLOAK_ROLE_MAP:
                return KEYCLOAK_ROLE_MAP[role]
        return payload.get("role", "operator")


def keycloak_token_to_payload(token: str) -> TokenPayload:
    """Convert validated Keycloak token to IPE TokenPayload."""
    validator = KeycloakTokenValidator()
    raw = validator.validate(token)
    role = validator.map_roles(raw)
    tenant_id = raw.get("tenant_id") or raw.get("org_id") or "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"
    return TokenPayload(
        sub=raw.get("sub", ""),
        tenant_id=tenant_id,
        role=role,
        type=raw.get("type", "access"),
        exp=raw.get("exp"),
        iat=raw.get("iat"),
        jti=raw.get("jti", ""),
        iss=raw.get("iss"),
        aud=raw.get("aud"),
        realm_access=raw.get("realm_access"),
    )
