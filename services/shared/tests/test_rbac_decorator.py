import pytest
from unittest.mock import AsyncMock, MagicMock

from fastapi import HTTPException

from ipe_shared.auth.rbac import require_permission, Role


class TestRBACDecorator:
    async def test_raises_401_when_no_user(self):
        @require_permission("read")
        async def fake_endpoint(current_user=None):
            return "ok"

        with pytest.raises(HTTPException) as exc:
            await fake_endpoint()
        assert exc.value.status_code == 401

    async def test_raises_403_when_permission_missing(self):
        @require_permission("admin")
        async def fake_endpoint(current_user=None):
            return "ok"

        current_user = MagicMock()
        current_user.role = "operator"

        with pytest.raises(HTTPException) as exc:
            await fake_endpoint(current_user=current_user)
        assert exc.value.status_code == 403
        assert "admin" in exc.value.detail

    async def test_passes_when_permission_granted(self):
        @require_permission("read")
        async def fake_endpoint(current_user=None):
            return "ok"

        current_user = MagicMock()
        current_user.role = "executive"

        result = await fake_endpoint(current_user=current_user)
        assert result == "ok"

    async def test_admin_has_all_permissions(self):
        for perm in ["read", "write", "approve", "admin", "delete"]:

            @require_permission(perm)
            async def fake_endpoint(current_user=None):
                return "ok"

            current_user = MagicMock()
            current_user.role = "admin"
            result = await fake_endpoint(current_user=current_user)
            assert result == "ok"

    async def test_operator_cannot_approve(self):
        @require_permission("approve")
        async def fake_endpoint(current_user=None):
            return "ok"

        current_user = MagicMock()
        current_user.role = "operator"

        with pytest.raises(HTTPException) as exc:
            await fake_endpoint(current_user=current_user)
        assert exc.value.status_code == 403
