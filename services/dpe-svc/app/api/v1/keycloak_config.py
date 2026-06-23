"""Keycloak configuration API endpoint."""
from __future__ import annotations

from fastapi import APIRouter

from ipe_shared.auth.keycloak_config import (
    IPE_REALM,
    OIDC_CLIENTS,
    TEST_USERS,
    generate_realm_json,
    get_demo_jwt_claims,
)

router = APIRouter(prefix="/keycloak", tags=["keycloak"])


@router.get("/realm")
async def get_realm_config() -> dict:
    return generate_realm_json()


@router.get("/clients")
async def list_clients() -> dict:
    return {
        "clients": [
            {"client_id": c.client_id, "name": c.name, "protocol": c.protocol}
            for c in OIDC_CLIENTS
        ]
    }


@router.get("/users")
async def list_test_users() -> dict:
    return {
        "users": [
            {"username": u.username, "email": u.email, "roles": u.roles, "tenant_id": u.tenant_id}
            for u in TEST_USERS
        ]
    }


@router.get("/demo-jwt/{username}")
async def get_demo_jwt(username: str) -> dict:
    claims = get_demo_jwt_claims(username)
    import base64
    import json
    header = base64.b64encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode()).decode()
    payload = base64.b64encode(json.dumps(claims).encode()).decode()
    signature = "demo-signature"
    token = f"{header}.{payload}.{signature}"
    return {"token": token, "claims": claims}
