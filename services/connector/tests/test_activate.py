import pytest
from uuid import uuid4


pytestmark = pytest.mark.integration


class TestActivateEndpoint:
    async def test_activate_no_tenant(self, client):
        r = await client.post(
            "/api/v1/sync/odoo/activate",
            json={
                "mo_ids": [],
                "odoo_url": "http://odoo:8069",
                "odoo_db": "test",
                "odoo_username": "admin",
                "odoo_password": "admin",
            },
        )
        assert r.status_code == 200
        body = r.json()
        assert body["error"]["code"] == "NO_TENANT"
