import pytest
from uuid import uuid4
from datetime import datetime, timezone

from ipe_shared.auth.jwt import create_access_token, create_refresh_token, decode_token


class TestJWT:
    def test_create_access_token(self):
        user_id = uuid4()
        tenant_id = uuid4()
        token = create_access_token(user_id, tenant_id, "planner")
        assert isinstance(token, str)
        assert len(token.split(".")) == 3

    def test_decode_access_token(self):
        user_id = uuid4()
        tenant_id = uuid4()
        token = create_access_token(user_id, tenant_id, "planner")
        payload = decode_token(token)
        assert payload.sub == str(user_id)
        assert payload.tenant_id == str(tenant_id)
        assert payload.role == "planner"
        assert payload.type == "access"

    def test_create_refresh_token(self):
        user_id = uuid4()
        tenant_id = uuid4()
        token = create_refresh_token(user_id, tenant_id, "admin")
        payload = decode_token(token)
        assert payload.sub == str(user_id)
        assert payload.type == "refresh"
