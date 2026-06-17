import pytest
from uuid import uuid4

from ipe_shared.auth.models import LoginRequest, LoginResponse, RefreshRequest, UserInfo


class TestAuthModels:
    def test_login_request(self):
        req = LoginRequest(email="admin@test.com", password="pass123")
        assert req.email == "admin@test.com"
        assert req.password == "pass123"

    def test_login_response(self):
        resp = LoginResponse(
            access_token="access123", refresh_token="refresh123", expires_in=3600
        )
        assert resp.access_token == "access123"
        assert resp.refresh_token == "refresh123"
        assert resp.token_type == "bearer"

    def test_refresh_request(self):
        req = RefreshRequest(refresh_token="old_token")
        assert req.refresh_token == "old_token"

    def test_user_info(self):
        uid = uuid4()
        tid = uuid4()
        info = UserInfo(
            id=uid, email="user@test.com", full_name="Alice", role="planner", tenant_id=tid
        )
        assert info.id == uid
        assert info.tenant_id == tid
        assert info.role == "planner"
