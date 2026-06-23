import pytest
from unittest.mock import MagicMock

from fastapi import HTTPException
from ipe_shared.auth.jwt import TokenPayload
from ipe_shared.auth.rbac import require_roles, require_any_permission, Role, PERMISSIONS


def _make_user(role: str = "planner") -> TokenPayload:
    return TokenPayload(
        sub="00000000-0000-0000-0000-000000000001",
        tenant_id="00000000-0000-0000-0000-000000000002",
        role=role,
        type="access",
        exp="2099-01-01T00:00:00Z",
        iat="2026-01-01T00:00:00Z",
        jti="test-jti",
    )


class TestRequireRoles:
    @pytest.mark.asyncio
    async def test_planner_access_planner_route(self):
        dep = require_roles(["planner", "admin"])
        user = _make_user("planner")
        result = await dep(current_user=user)
        assert result.role == "planner"

    @pytest.mark.asyncio
    async def test_admin_access_planner_route(self):
        dep = require_roles(["planner", "admin"])
        user = _make_user("admin")
        result = await dep(current_user=user)
        assert result.role == "admin"

    @pytest.mark.asyncio
    async def test_supervisor_denied_planner_route(self):
        dep = require_roles(["planner", "admin"])
        user = _make_user("supervisor")
        with pytest.raises(HTTPException) as exc_info:
            await dep(current_user=user)
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_auditor_denied_write_route(self):
        dep = require_roles(["planner", "admin"])
        user = _make_user("auditor")
        with pytest.raises(HTTPException) as exc_info:
            await dep(current_user=user)
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_case_insensitive_role_match(self):
        dep = require_roles(["PLANNER", "ADMIN"])
        user = _make_user("planner")
        result = await dep(current_user=user)
        assert result.role == "planner"

    @pytest.mark.asyncio
    async def test_supervisor_can_access_copilot(self):
        dep = require_roles(["planner", "admin", "manager", "supervisor"])
        user = _make_user("supervisor")
        result = await dep(current_user=user)
        assert result.role == "supervisor"

    @pytest.mark.asyncio
    async def test_auditor_can_access_audit_logs(self):
        dep = require_roles(["planner", "admin", "manager", "auditor", "executive"])
        user = _make_user("auditor")
        result = await dep(current_user=user)
        assert result.role == "auditor"


class TestRequireAnyPermission:
    @pytest.mark.asyncio
    async def test_planner_has_approve(self):
        dep = require_any_permission("approve", "admin")
        user = _make_user("planner")
        result = await dep(current_user=user)
        assert result.role == "planner"

    @pytest.mark.asyncio
    async def test_executive_denied_approve(self):
        dep = require_any_permission("approve", "admin")
        user = _make_user("executive")
        with pytest.raises(HTTPException) as exc_info:
            await dep(current_user=user)
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_auditor_has_view_audit_logs(self):
        dep = require_any_permission("view_audit_logs", "view_kpis")
        user = _make_user("auditor")
        result = await dep(current_user=user)
        assert result.role == "auditor"

    @pytest.mark.asyncio
    async def test_operator_denied_view_audit_logs(self):
        dep = require_any_permission("view_audit_logs")
        user = _make_user("operator")
        with pytest.raises(HTTPException) as exc_info:
            await dep(current_user=user)
        assert exc_info.value.status_code == 403
