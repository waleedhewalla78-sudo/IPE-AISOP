from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ipe_shared.auth.jwt import TokenPayload, decode_token

try:
    from ipe_shared.auth.keycloak import auth_provider, keycloak_token_to_payload
except ImportError:
    def auth_provider() -> str:
        return "local"

    def keycloak_token_to_payload(token: str) -> TokenPayload:
        raise RuntimeError("Keycloak module unavailable")

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> TokenPayload:
    try:
        if auth_provider() == "keycloak":
            payload = keycloak_token_to_payload(credentials.credentials)
        else:
            payload = decode_token(credentials.credentials)
        if payload.type != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )
        return payload
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )


async def get_tenant_id(
    current_user: TokenPayload = Depends(get_current_user),
) -> UUID:
    return current_user.tenant_id
