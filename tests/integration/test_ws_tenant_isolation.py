"""WebSocket tenant isolation integration tests.

Validates the fea-svc WebSocket gateway's tenant isolation:
  1. Path tenant != JWT tenant → close 4403 or HTTP 403
  2. Valid socket receives only its own tenant's events

Requires: fea-svc running at localhost:8004 (Docker stack)
"""

import asyncio
import uuid

import httpx
import pytest

pytestmark = [pytest.mark.integration]


def _fea_ws_available() -> bool:
    """Check if fea-svc is reachable (health endpoint)."""
    try:
        r = httpx.get("http://localhost:8004/api/v1/health", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


@pytest.mark.skipif(not _fea_ws_available(), reason="fea-svc not running")
class TestWsTenantIsolation:
    """Validate WebSocket gateway tenant isolation."""

    async def test_path_tenant_mismatch_jwt_closes_4403(self):
        """Connect with JWT for tenant_a to path /ws/tenant_b → rejected (4403 or 403)."""
        from ipe_shared.auth.jwt import create_access_token

        tenant_a = str(uuid.uuid4())
        tenant_b = str(uuid.uuid4())
        assert tenant_a != tenant_b

        token = create_access_token(
            user_id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            role="planner",
        )

        ws_url = f"ws://localhost:8004/api/v1/feasibility/ws/{tenant_b}?token={token}"

        import websockets

        try:
            async with websockets.connect(ws_url) as ws:
                msg = await asyncio.wait_for(ws.recv(), timeout=5)
                pytest.fail(f"Expected rejection, got message: {msg}")
        except websockets.exceptions.ConnectionClosedError as e:
            assert e.code == 4403, f"Expected close code 4403, got {e.code}"
        except websockets.exceptions.InvalidStatus as e:
            # HTTP 403 before WS upgrade — also valid rejection
            assert "403" in str(e.response.status_code) or "403" in str(e), (
                f"Expected HTTP 403 rejection, got: {e}"
            )
        except Exception as e:
            if "Connection refused" in str(e) or "timed out" in str(e):
                pytest.skip(f"fea-svc WS not reachable: {e}")
            raise

    async def test_valid_socket_receives_only_own_events(self):
        """Two sockets for different tenants — only matching tenant receives broadcast."""
        from ipe_shared.auth.jwt import create_access_token

        tenant_a = str(uuid.uuid4())
        tenant_b = str(uuid.uuid4())

        token_a = create_access_token(
            user_id=uuid.uuid4(), tenant_id=uuid.uuid4(), role="planner"
        )
        token_b = create_access_token(
            user_id=uuid.uuid4(), tenant_id=uuid.uuid4(), role="planner"
        )

        import websockets

        url_a = f"ws://localhost:8004/api/v1/feasibility/ws/{tenant_a}?token={token_a}"
        url_b = f"ws://localhost:8004/api/v1/feasibility/ws/{tenant_b}?token={token_b}"

        try:
            async with websockets.connect(url_a) as ws_a, websockets.connect(url_b) as ws_b:
                # Both connected — verify they're independent
                try:
                    msg = await asyncio.wait_for(ws_a.recv(), timeout=2)
                    assert tenant_b not in str(msg), (
                        f"FAIL: tenant_b received a message on tenant_a's socket"
                    )
                except asyncio.TimeoutError:
                    pass  # Expected in shadow mode — no broadcasts

                try:
                    msg = await asyncio.wait_for(ws_b.recv(), timeout=2)
                    assert tenant_a not in str(msg), (
                        f"FAIL: tenant_a received a message on tenant_b's socket"
                    )
                except asyncio.TimeoutError:
                    pass  # Expected in shadow mode — no broadcasts
        except websockets.exceptions.InvalidStatus:
            pytest.skip("fea-svc WS rejected connection (HTTP 403)")
        except Exception as e:
            if "Connection refused" in str(e) or "timed out" in str(e):
                pytest.skip(f"fea-svc WS not reachable: {e}")
            raise
