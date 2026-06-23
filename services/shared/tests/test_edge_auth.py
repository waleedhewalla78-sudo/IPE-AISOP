import hashlib
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from ipe_shared.auth.edge_auth import EdgeGatewayAuth


class TestEdgeGatewayAuth:
    @pytest.fixture
    def auth(self):
        return EdgeGatewayAuth(require_mtls=False)

    @pytest.fixture
    def mtls_auth(self):
        return EdgeGatewayAuth(require_mtls=True)

    def test_extract_cert_serial(self, auth):
        cert_pem = """-----BEGIN CERTIFICATE-----
MIIBkTCB+wIJALHM5P1v4R4vMA0GCSqGSIb3DQEBCwUAMBExDzANBgNVBAMMBnRl
-----END CERTIFICATE-----"""
        serial = auth._extract_cert_serial(cert_pem)
        assert len(serial) == 16

    def test_extract_cert_serial_invalid(self, auth):
        serial = auth._extract_cert_serial("invalid-cert")
        assert serial == "unknown"

    def test_invalidate_cache(self, auth):
        auth._gateway_cache["gw-001"] = {"gateway_id": "gw-001"}
        auth.invalidate_cache("gw-001")
        assert "gw-001" not in auth._gateway_cache

    @pytest.mark.asyncio
    async def test_authenticate_missing_gateway_id(self, auth):
        request = MagicMock()
        request.headers = {}

        with pytest.raises(Exception) as exc_info:
            await auth.authenticate(request, api_key="test-key")
        assert "X-Gateway-ID" in str(exc_info.value) or "Missing" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_authenticate_missing_api_key(self, auth):
        request = MagicMock()
        request.headers = {"X-Gateway-ID": "gw-001"}

        with pytest.raises(Exception) as exc_info:
            await auth.authenticate(request, api_key=None)
        assert "API key" in str(exc_info.value) or "Missing" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_authenticate_mtls_missing_cert(self, mtls_auth):
        request = MagicMock()
        request.headers = {"X-Gateway-ID": "gw-001"}

        with pytest.raises(Exception) as exc_info:
            await mtls_auth.authenticate(request, api_key=None)
        assert "mTLS" in str(exc_info.value) or "certificate" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_authenticate_cached_gateway(self, auth):
        api_key = "test-api-key-123"
        api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()

        auth._gateway_cache["gw-001"] = {
            "gateway_id": "gw-001",
            "gateway_name": "Test Gateway",
            "tenant_id": "tenant-001",
            "is_active": True,
            "api_key_hash": api_key_hash,
        }

        request = MagicMock()
        request.headers = {"X-Gateway-ID": "gw-001"}

        result = await auth.authenticate(request, api_key=api_key)
        assert result["gateway_id"] == "gw-001"

    @pytest.mark.asyncio
    async def test_authenticate_invalid_api_key_cached(self, auth):
        api_key = "correct-key"
        api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()

        auth._gateway_cache["gw-001"] = {
            "gateway_id": "gw-001",
            "gateway_name": "Test Gateway",
            "tenant_id": "tenant-001",
            "is_active": True,
            "api_key_hash": api_key_hash,
        }

        request = MagicMock()
        request.headers = {"X-Gateway-ID": "gw-001"}

        with pytest.raises(Exception) as exc_info:
            await auth.authenticate(request, api_key="wrong-key")
        assert "Invalid API key" in str(exc_info.value) or "500" in str(exc_info.value)
