from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import jwt
from pydantic import BaseModel

from ipe_shared.auth.jwks import JWKSAuthBackend, JWKSConfig
from ipe_shared.auth.jwt_keys import (
    get_key_id,
    get_private_key_pem,
    get_public_key_for_kid,
    use_rs256_signing,
)
from ipe_shared.config import settings


class AuthenticationError(Exception):
  """Raised when JWT validation fails."""


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


def _base_payload(user_id: UUID, tenant_id: UUID, role: str, token_type: str, expires_minutes: int) -> dict[str, Any]:
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "tenant_id": str(tenant_id),
        "role": role,
        "exp": now + timedelta(minutes=expires_minutes),
        "iat": now,
        "jti": str(uuid4()),
        "type": token_type,
    }
    keycloak_url = getattr(settings, "KEYCLOAK_URL", "")
    if keycloak_url:
        realm = getattr(settings, "KEYCLOAK_REALM", "ipe")
        payload["iss"] = f"{keycloak_url}/realms/{realm}"
        payload["aud"] = "ipe-platform"
    return payload


def _encode_payload(payload: dict[str, Any]) -> str:
    if use_rs256_signing():
        kid = get_key_id()
        return jwt.encode(
            payload,
            get_private_key_pem(),
            algorithm="RS256",
            headers={"kid": kid},
        )
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_access_token(user_id: UUID, tenant_id: UUID, role: str) -> str:
    payload = _base_payload(
        user_id,
        tenant_id,
        role,
        "access",
        settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
    )
    return _encode_payload(payload)


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
    payload = _base_payload(
        user_id,
        tenant_id,
        role,
        "refresh",
        settings.JWT_REFRESH_TOKEN_EXPIRE_MINUTES,
    )
    return _encode_payload(payload)


def _decode_local_token(token: str) -> dict[str, Any]:
    header = jwt.get_unverified_header(token)
    algorithm = header.get("alg", settings.JWT_ALGORITHM)

    if algorithm == "RS256" or use_rs256_signing():
        kid = header.get("kid")
        public_key = get_public_key_for_kid(kid)
        return jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            options={"require": ["sub", "tenant_id", "exp", "iat", "jti"]},
        )

    return jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
        options={"require": ["sub", "tenant_id", "exp", "iat"]},
    )


def decode_token(token: str) -> TokenPayload:
    use_jwks = getattr(settings, "JWT_USE_JWKS", False)

    if use_jwks:
        config = JWKSConfig.from_settings()
        backend = JWKSAuthBackend(config)
        try:
            payload = backend.validate_token(token)
        except jwt.PyJWTError as exc:
            raise AuthenticationError(str(exc)) from exc

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

    try:
        payload = _decode_local_token(token)
    except jwt.ExpiredSignatureError as exc:
        raise AuthenticationError("Token expired") from exc
    except jwt.InvalidTokenError as exc:
        raise AuthenticationError(f"Invalid token: {exc}") from exc

    return TokenPayload(**payload)
