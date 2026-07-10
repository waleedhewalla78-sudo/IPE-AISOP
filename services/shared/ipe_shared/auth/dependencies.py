from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ipe_shared.auth.jwt import TokenPayload, decode_token
from ipe_shared.auth.jwt_keys import get_key_id
from ipe_shared.auth.token_blacklist import is_token_blacklisted

try:
    from ipe_shared.auth.keycloak import auth_provider, keycloak_token_to_payload
except ImportError:
    def auth_provider() -> str:
        return "local"

    def keycloak_token_to_payload(token: str) -> TokenPayload:
        raise RuntimeError("Keycloak module unavailable")

security = HTTPBearer()


def _resolve_token_payload(token: str) -> TokenPayload:
    """Verify JWT: local RS256 (login) first when kid matches, else Keycloak JWKS."""
    header = jwt.get_unverified_header(token)
    kid = header.get("kid")
    local_kid = get_key_id()

    # Platform login issues RS256 with IPE_JWT_KEY_ID even when AUTH_MODE=keycloak.
    if kid == local_kid or auth_provider() != "keycloak":
        return decode_token(token)

    try:
        return keycloak_token_to_payload(token)
    except Exception:
        # Hybrid stacks: fall back to local public key when Keycloak JWKS lacks the kid.
        return decode_token(token)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> TokenPayload:
    try:
        payload = _resolve_token_payload(credentials.credentials)
        if payload.jti and await is_token_blacklisted(payload.jti):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token revoked",
            )
        if payload.type != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )
        return payload
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )


async def get_tenant_id(
    current_user: TokenPayload = Depends(get_current_user),
) -> UUID:
    return current_user.tenant_id
