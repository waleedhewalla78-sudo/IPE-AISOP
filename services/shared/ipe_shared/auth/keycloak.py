"""
Keycloak SSO integration for IPE platform.

Handles token verification (JWKS), OAuth code exchange, and user provisioning.
Activation: AUTH_MODE=keycloak (or AUTH_PROVIDER=keycloak) + KEYCLOAK_URL.
"""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx
import jwt
from jwt import PyJWKClient

from ipe_shared.auth.jwt import TokenPayload
from ipe_shared.config import settings

logger = logging.getLogger(__name__)

IPE_ROLES = frozenset({
    "admin", "planner", "manager", "supervisor", "operator",
    "auditor", "executive", "viewer", "procurement", "system",
})

KEYCLOAK_ROLE_MAP: dict[str, str] = {
    "ipe_admin": "admin",
    "ipe-admin": "admin",
    "ipe_planner": "planner",
    "ipe-planner": "planner",
    "ipe_manager": "manager",
    "ipe-manager": "manager",
    "ipe_supervisor": "supervisor",
    "ipe_executive": "executive",
    "ipe_procurement": "procurement",
    "ipe_viewer": "viewer",
    "ipe_system": "system",
    "ipe_operator": "operator",
}


def auth_provider() -> str:
    mode = os.getenv("AUTH_MODE") or os.getenv("AUTH_PROVIDER") or getattr(settings, "AUTH_MODE", "local")
    return str(mode).lower()


def _keycloak_url() -> str:
    return (os.getenv("KEYCLOAK_URL") or getattr(settings, "KEYCLOAK_URL", "") or "").rstrip("/")


def _keycloak_realm() -> str:
    return os.getenv("KEYCLOAK_REALM") or getattr(settings, "KEYCLOAK_REALM", "ipe")


def _keycloak_client_id() -> str:
    return os.getenv("KEYCLOAK_CLIENT_ID") or getattr(settings, "KEYCLOAK_CLIENT_ID", "ipe-platform")


def _keycloak_client_secret() -> str:
    return os.getenv("KEYCLOAK_CLIENT_SECRET") or getattr(settings, "KEYCLOAK_CLIENT_SECRET", "")


_jwks_client: PyJWKClient | None = None


def get_keycloak_jwks_client() -> PyJWKClient:
    global _jwks_client
    if _jwks_client is None:
        base = _keycloak_url()
        if not base:
            raise RuntimeError("KEYCLOAK_URL is not configured")
        jwks_url = f"{base}/realms/{_keycloak_realm()}/protocol/openid-connect/certs"
        _jwks_client = PyJWKClient(jwks_url, cache_keys=True)
    return _jwks_client


def map_keycloak_roles(payload: dict[str, Any]) -> str:
    realm_access = payload.get("realm_access", {})
    roles: list[str] = []
    if isinstance(realm_access, dict):
        roles = list(realm_access.get("roles") or [])
    roles.extend(payload.get("roles") or [])

    for role in roles:
        mapped = KEYCLOAK_ROLE_MAP.get(role)
        if mapped:
            return mapped
        if role in IPE_ROLES:
            return role
    return str(payload.get("role", "operator"))


def _extract_tenant_id(payload: dict[str, Any]) -> str:
    tenant = payload.get("tenant_id")
    if isinstance(tenant, list) and tenant:
        return str(tenant[0])
    if tenant:
        return str(tenant)
    return str(payload.get("org_id") or "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11")


async def verify_keycloak_token(token: str) -> dict[str, Any]:
    """Verify a Keycloak-issued JWT using JWKS."""
    jwks_client = get_keycloak_jwks_client()
    signing_key = jwks_client.get_signing_key_from_jwt(token)
    payload = jwt.decode(
        token,
        signing_key.key,
        algorithms=["RS256"],
        options={"verify_aud": False, "require": ["sub", "exp", "iat"]},
    )
    return {
        "sub": payload["sub"],
        "tenant_id": _extract_tenant_id(payload),
        "email": payload.get("email"),
        "name": payload.get("name") or payload.get("preferred_username"),
        "roles": payload.get("realm_access", {}).get("roles", []) if isinstance(payload.get("realm_access"), dict) else [],
        "role": map_keycloak_roles(payload),
        "preferred_username": payload.get("preferred_username"),
        "exp": payload.get("exp"),
        "iat": payload.get("iat"),
        "jti": payload.get("jti"),
        "token_source": "keycloak",
        "raw": payload,
    }


def keycloak_token_to_payload(token: str) -> TokenPayload:
    """Sync wrapper used by FastAPI dependencies (JWKS fetch is sync in PyJWKClient)."""
    jwks_client = get_keycloak_jwks_client()
    signing_key = jwks_client.get_signing_key_from_jwt(token)
    raw = jwt.decode(
        token,
        signing_key.key,
        algorithms=["RS256"],
        options={"verify_aud": False, "require": ["sub", "exp", "iat"]},
    )
    role = map_keycloak_roles(raw)
    return TokenPayload(
        sub=raw.get("sub", ""),
        tenant_id=_extract_tenant_id(raw),
        role=role,
        type="access",
        exp=raw.get("exp"),
        iat=raw.get("iat"),
        jti=raw.get("jti", ""),
        iss=raw.get("iss"),
        aud=raw.get("aud"),
        realm_access=raw.get("realm_access"),
    )


async def _admin_token() -> str:
    base = _keycloak_url()
    admin_user = os.getenv("KEYCLOAK_ADMIN_USER", "admin")
    admin_pass = os.getenv("KEYCLOAK_ADMIN_PASSWORD", "admin")
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(
            f"{base}/realms/master/protocol/openid-connect/token",
            data={
                "grant_type": "password",
                "client_id": "admin-cli",
                "username": admin_user,
                "password": admin_pass,
            },
        )
        resp.raise_for_status()
        return resp.json()["access_token"]


async def get_keycloak_user(user_id: str) -> dict[str, Any]:
    base = _keycloak_url()
    token = await _admin_token()
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(
            f"{base}/admin/realms/{_keycloak_realm()}/users/{user_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        resp.raise_for_status()
        return resp.json()


async def create_keycloak_user(
    username: str,
    email: str,
    tenant_id: str,
    roles: list[str],
    password: str,
) -> dict[str, Any]:
    base = _keycloak_url()
    token = await _admin_token()
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(
            f"{base}/admin/realms/{_keycloak_realm()}/users",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "username": username,
                "email": email,
                "enabled": True,
                "attributes": {"tenant_id": [tenant_id]},
                "credentials": [{"type": "password", "value": password, "temporary": True}],
            },
        )
        if resp.status_code not in (201, 409):
            resp.raise_for_status()
        return {"status": "created", "username": username, "roles": roles}


async def exchange_code_for_token(code: str, redirect_uri: str) -> dict[str, Any]:
    base = _keycloak_url()
    data = {
        "grant_type": "authorization_code",
        "client_id": _keycloak_client_id(),
        "code": code,
        "redirect_uri": redirect_uri,
    }
    secret = _keycloak_client_secret()
    if secret:
        data["client_secret"] = secret
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(
            f"{base}/realms/{_keycloak_realm()}/protocol/openid-connect/token",
            data=data,
        )
        resp.raise_for_status()
        return resp.json()


def _public_keycloak_url() -> str:
    override = os.getenv("KEYCLOAK_PUBLIC_URL") or getattr(settings, "KEYCLOAK_PUBLIC_URL", "")
    if override:
        return str(override).rstrip("/")
    base = _keycloak_url()
    if "keycloak:8080" in base:
        return base.replace("keycloak:8080", "localhost:8180")
    return base or "http://localhost:8180"


def auth_info() -> dict[str, Any]:
    """Return auth configuration for frontend bootstrap."""
    mode = auth_provider()
    return {
        "mode": mode,
        "keycloak_url": _public_keycloak_url() if mode == "keycloak" else "",
        "keycloak_realm": _keycloak_realm(),
        "keycloak_client_id": _keycloak_client_id(),
    }


# Backward-compatible exports
class KeycloakTokenValidator:
    def validate(self, token: str) -> dict[str, Any]:
        return keycloak_token_to_payload(token).model_dump()

    def map_roles(self, payload: dict[str, Any]) -> str:
        return map_keycloak_roles(payload)
