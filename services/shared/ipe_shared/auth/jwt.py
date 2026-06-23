from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import jwt
from pydantic import BaseModel

from ipe_shared.auth.jwks import JWKSAuthBackend, JWKSConfig
from ipe_shared.config import settings


class TokenPayload(BaseModel):
    sub: UUID | str
    tenant_id: UUID | str
    role: str
    type: str = "access"
    exp: datetime | None = None
    iat: datetime | None = None
    jti: str | None = None
    iss: str | None = None
    aud: str | None = None
    realm_access: dict | None = None


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


def create_access_token(user_id: UUID, tenant_id: UUID, role: str) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "tenant_id": str(tenant_id),
        "role": role,
        "exp": now + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES),
        "iat": now,
        "jti": str(uuid4()),
        "type": "access",
    }
    keycloak_url = getattr(settings, "KEYCLOAK_URL", "")
    if keycloak_url:
        realm = getattr(settings, "KEYCLOAK_REALM", "ipe")
        payload["iss"] = f"{keycloak_url}/realms/{realm}"
        payload["aud"] = "ipe-platform"
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_access_token_jwks(
    user_id: UUID,
    tenant_id: UUID,
    role: str,
    private_key: str | bytes,
    kid: str | None = None,
) -> str:
    now = datetime.now(UTC)
    headers: dict[str, str] = {}
    if kid:
        headers["kid"] = kid
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "tenant_id": str(tenant_id),
        "role": role,
        "exp": now + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES),
        "iat": now,
        "jti": str(uuid4()),
        "type": "access",
    }
    keycloak_url = getattr(settings, "KEYCLOAK_URL", "")
    if keycloak_url:
        realm = getattr(settings, "KEYCLOAK_REALM", "ipe")
        payload["iss"] = f"{keycloak_url}/realms/{realm}"
        payload["aud"] = "ipe-platform"
    return jwt.encode(payload, private_key, algorithm="RS256", headers=headers or None)


def create_refresh_token(user_id: UUID, tenant_id: UUID, role: str) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "tenant_id": str(tenant_id),
        "role": role,
        "exp": now + timedelta(minutes=settings.JWT_REFRESH_TOKEN_EXPIRE_MINUTES),
        "iat": now,
        "jti": str(uuid4()),
        "type": "refresh",
    }
    keycloak_url = getattr(settings, "KEYCLOAK_URL", "")
    if keycloak_url:
        realm = getattr(settings, "KEYCLOAK_REALM", "ipe")
        payload["iss"] = f"{keycloak_url}/realms/{realm}"
        payload["aud"] = "ipe-platform"
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> TokenPayload:
    use_jwks = getattr(settings, "JWT_USE_JWKS", False)

    if use_jwks:
        config = JWKSConfig.from_settings()
        backend = JWKSAuthBackend(config)
        payload = backend.validate_token(token)

        roles = []
        realm_access = payload.get("realm_access", {})
        if isinstance(realm_access, dict):
            roles = realm_access.get("roles", [])

        role = roles[0] if roles else payload.get("role", "operator")
        tenant_id = payload.get("tenant_id", "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11")

        return TokenPayload(
            sub=payload.get("sub", ""),
            tenant_id=tenant_id,
            role=role,
            type=payload.get("type", "access"),
            exp=payload.get("exp"),
            iat=payload.get("iat"),
            jti=payload.get("jti", ""),
            iss=payload.get("iss"),
            aud=payload.get("aud"),
            realm_access=realm_access,
        )
    else:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return TokenPayload(**payload)