import hashlib

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ipe_shared.auth.dependencies import get_current_user
from ipe_shared.auth.jwt import TokenPayload, create_access_token, create_refresh_token
from ipe_shared.config import settings
from ipe_shared.database.session import get_session
from ipe_shared.schemas.auth import LoginRequest, LoginResponse, UserInfo
from ipe_shared.schemas.common import APIResponse

router = APIRouter(prefix="/auth", tags=["auth"])

DEMO_TENANT_ID = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"
DEV_PASSWORDS = frozenset({"demo", "admin"})


def _verify_password(password: str, password_hash: str | None) -> bool:
    if password_hash and password_hash.startswith("{SHA-256}"):
        digest = hashlib.sha256(password.encode()).hexdigest()
        return password_hash == f"{{SHA-256}}{digest}"
    if settings.ENVIRONMENT != "production" and password in DEV_PASSWORDS:
        return True
    return False


async def _lookup_user(session: AsyncSession, email: str) -> dict | None:
    await session.execute(
        text("SELECT set_config('app.current_tenant_id', :tid, true)"),
        {"tid": DEMO_TENANT_ID},
    )
    result = await session.execute(
        text(
            """
            SELECT id, tenant_id, email, full_name, role, password_hash, is_active
            FROM cdm_user
            WHERE lower(email) = lower(:email)
            LIMIT 1
            """
        ),
        {"email": email.strip()},
    )
    row = result.mappings().one_or_none()
    return dict(row) if row else None


@router.post("/login", response_model=APIResponse[LoginResponse])
async def login(
    body: LoginRequest,
    session: AsyncSession = Depends(get_session),
) -> APIResponse[LoginResponse]:
    user = await _lookup_user(session, body.email)
    if not user or not user.get("is_active"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not _verify_password(body.password, user.get("password_hash")):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    user_id = UUID(str(user["id"]))
    tenant_id = UUID(str(user["tenant_id"]))
    role = str(user["role"])

    access_token = create_access_token(user_id, tenant_id, role)
    refresh_token = create_refresh_token(user_id, tenant_id, role)

    return APIResponse(
        data=LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
    )


@router.get("/me", response_model=APIResponse[UserInfo])
async def me(
    current_user: TokenPayload = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> APIResponse[UserInfo]:
    result = await session.execute(
        text(
            """
            SELECT id, tenant_id, email, full_name, role
            FROM cdm_user
            WHERE id = :user_id
            LIMIT 1
            """
        ),
        {"user_id": str(current_user.sub)},
    )
    row = result.mappings().one_or_none()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return APIResponse(
        data=UserInfo(
            id=UUID(str(row["id"])),
            email=str(row["email"]),
            full_name=str(row["full_name"] or row["email"]),
            role=str(row["role"]),
            tenant_id=UUID(str(row["tenant_id"])),
        )
    )
