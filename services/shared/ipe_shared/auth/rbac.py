from enum import Enum
from functools import wraps

from fastapi import HTTPException, status


class Role(str, Enum):
    ADMIN = "admin"
    PLANNER = "planner"
    OPERATOR = "operator"
    MANAGER = "manager"
    EXECUTIVE = "executive"


PERMISSIONS = {
    Role.ADMIN: {"read", "write", "approve", "admin", "delete"},
    Role.PLANNER: {"read", "write", "approve"},
    Role.MANAGER: {"read", "write", "approve"},
    Role.OPERATOR: {"read", "write_own"},
    Role.EXECUTIVE: {"read"},
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
