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
    """Verify JWT for hybrid stacks: local RS256 login and Keycloak SSO.

    - Tokens with the platform key id always use local RS256 verification.
    - AUTH_MODE=keycloak: verify other tokens via JWKS, with local fallback.
    - AUTH_MODE=local: try local first, then Keycloak JWKS so SSO still works.
    """
    header = jwt.get_unverified_header(token)
    kid = header.get("kid")
    local_kid = get_key_id()

    if kid == local_kid:
        return decode_token(token)

    if auth_provider() == "keycloak":
        try:
            return keycloak_token_to_payload(token)
        except Exception:
            # Hybrid stacks: fall back to local public key when Keycloak JWKS lacks the kid.
            return decode_token(token)

    # AUTH_MODE=local (R2 compose): accept platform login, then Keycloak SSO tokens.
    try:
        return decode_token(token)
    except Exception:
        return keycloak_token_to_payload(token)


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
