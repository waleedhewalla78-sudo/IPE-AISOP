import pytest
from ipe_shared.auth.rbac import Role, PERMISSIONS


class TestRBAC:
    def test_admin_permissions(self):
        perms = PERMISSIONS[Role.ADMIN]
        assert "read" in perms
        assert "write" in perms
        assert "delete" in perms
        assert "admin" in perms

    def test_planner_permissions(self):
        perms = PERMISSIONS[Role.PLANNER]
        assert "read" in perms
        assert "write" in perms
        assert "approve" in perms
        assert "delete" not in perms

    def test_operator_no_write(self):
        perms = PERMISSIONS[Role.OPERATOR]
        assert "read" in perms
        assert "write_own" in perms
        assert "write" not in perms
        assert "approve" not in perms

    def test_executive_readonly(self):
        perms = PERMISSIONS[Role.EXECUTIVE]
        assert "read" in perms
        assert "write" not in perms
