from enum import StrEnum
from functools import wraps

from fastapi import Depends, HTTPException, status

from ipe_shared.auth.dependencies import get_current_user
from ipe_shared.auth.jwt import TokenPayload


class Role(StrEnum):
    ADMIN = "admin"
    PLANNER = "planner"
    SUPERVISOR = "supervisor"
    AUDITOR = "auditor"
    OPERATOR = "operator"
    MANAGER = "manager"
    EXECUTIVE = "executive"
    PROCUREMENT = "procurement"


PERMISSIONS = {
    Role.ADMIN: {"read", "write", "approve", "admin", "delete", "run_solver", "cost_optimize", "manage_users"},
    Role.PLANNER: {"read", "write", "approve", "run_solver", "cost_optimize", "view_copilot", "run_scenario"},
    Role.SUPERVISOR: {"read", "acknowledge_disruption", "view_schedule", "view_copilot"},
    Role.AUDITOR: {"read", "view_audit_logs", "view_kpis", "view_scenarios"},
    Role.MANAGER: {"read", "write", "approve", "run_solver", "cost_optimize"},
    Role.OPERATOR: {"read", "write_own"},
    Role.EXECUTIVE: {"read", "view_kpis"},
    Role.PROCUREMENT: {"read", "write", "view_kpis"},
}


def require_permission(permission: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, current_user=None, **kwargs):
            if current_user is None:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
            user_perms = PERMISSIONS.get(Role(current_user.role), set())
            if permission not in user_perms:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission '{permission}' required. Role '{current_user.role}' insufficient.",
                )
            return await func(*args, current_user=current_user, **kwargs)

        return wrapper

    return decorator


def require_roles(allowed_roles: list[str]):
    """FastAPI dependency that enforces role-based access control.

    Usage:
        @router.post("/schedule")
        async def schedule(
            current_user: TokenPayload = Depends(require_roles(["planner", "admin"])),
        ):
            ...
    """
    async def _check(
        current_user: TokenPayload = Depends(get_current_user),
    ) -> TokenPayload:
        user_role = current_user.role.lower()
        allowed_lower = [r.lower() for r in allowed_roles]
        if user_role not in allowed_lower:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{current_user.role}' not in allowed roles: {allowed_roles}",
            )
        return current_user

    return _check


def require_any_permission(*permissions: str):
    """FastAPI dependency that checks user has ANY of the listed permissions."""
    async def _check(
        current_user: TokenPayload = Depends(get_current_user),
    ) -> TokenPayload:
        user_perms = PERMISSIONS.get(Role(current_user.role), set())
        if not user_perms.intersection(set(permissions)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"One of permissions {list(permissions)} required. Role '{current_user.role}' insufficient.",
            )
        return current_user

    return _check
