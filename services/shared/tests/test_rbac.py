import pytest
from ipe_shared.auth.rbac import Role, PERMISSIONS


class TestRBAC:
    def test_admin_permissions(self):
        perms = PERMISSIONS[Role.ADMIN]
        assert "read" in perms
        assert "write" in perms
        assert "delete" in perms
        assert "admin" in perms
        assert "run_solver" in perms
        assert "cost_optimize" in perms

    def test_planner_permissions(self):
        perms = PERMISSIONS[Role.PLANNER]
        assert "read" in perms
        assert "write" in perms
        assert "approve" in perms
        assert "run_solver" in perms
        assert "cost_optimize" in perms
        assert "view_copilot" in perms
        assert "delete" not in perms

    def test_supervisor_permissions(self):
        perms = PERMISSIONS[Role.SUPERVISOR]
        assert "read" in perms
        assert "view_schedule" in perms
        assert "acknowledge_disruption" in perms
        assert "view_copilot" in perms
        assert "write" not in perms
        assert "approve" not in perms

    def test_auditor_permissions(self):
        perms = PERMISSIONS[Role.AUDITOR]
        assert "read" in perms
        assert "view_audit_logs" in perms
        assert "view_kpis" in perms
        assert "view_scenarios" in perms
        assert "write" not in perms
        assert "approve" not in perms

    def test_operator_no_write(self):
        perms = PERMISSIONS[Role.OPERATOR]
        assert "read" in perms
        assert "write_own" in perms
        assert "write" not in perms
        assert "approve" not in perms

    def test_executive_readonly(self):
        perms = PERMISSIONS[Role.EXECUTIVE]
        assert "read" in perms
        assert "view_kpis" in perms
        assert "write" not in perms

    def test_all_roles_have_read(self):
        for role in Role:
            assert "read" in PERMISSIONS[role], f"{role} missing read permission"

    def test_new_roles_defined(self):
        assert hasattr(Role, "SUPERVISOR")
        assert hasattr(Role, "AUDITOR")
        assert Role.SUPERVISOR.value == "supervisor"
        assert Role.AUDITOR.value == "auditor"
