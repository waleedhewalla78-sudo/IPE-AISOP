"""Edge Gateway Security Middleware.

This module provides authentication and authorization for Edge Gateways,
supporting both mTLS (Mutual TLS) and API key authentication.
"""
import hashlib
import logging
import ssl
from typing import Any

from fastapi import HTTPException, Request, Security
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials
from sqlalchemy import select as sa_select
from sqlalchemy.ext.asyncio import AsyncSession

from ipe_shared.database.session import get_session as get_db_session
from ipe_shared.middleware.tenant_context import tenant_ctx
from ipe_shared.models.edge_sync import EdgeGateway

logger = logging.getLogger(__name__)

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)
GATEWAY_ID_HEADER = "X-Gateway-ID"


class EdgeGatewayAuth:
    """Authentication handler for Edge Gateways."""

    def __init__(
        self,
        require_mtls: bool = False,
        mtls_client_ca: str | None = None,
    ):
        self.require_mtls = require_mtls
        self.mtls_client_ca = mtls_client_ca
        self._gateway_cache: dict[str, dict[str, Any]] = {}

    async def authenticate(
        self,
        request: Request,
        api_key: str | None = Security(API_KEY_HEADER),
        session: AsyncSession | None = None,
    ) -> dict[str, Any]:
        gateway_id = request.headers.get(GATEWAY_ID_HEADER)
        if not gateway_id:
            raise HTTPException(
                status_code=401,
                detail="Missing X-Gateway-ID header",
            )

        if self.require_mtls:
            return await self._authenticate_mtls(request, gateway_id, session)
        else:
            return await self._authenticate_api_key(request, gateway_id, api_key, session)

    async def _authenticate_api_key(
        self,
        request: Request,
        gateway_id: str,
        api_key: str | None,
        session: AsyncSession | None = None,
    ) -> dict[str, Any]:
        if not api_key:
            raise HTTPException(
                status_code=401,
                detail="Missing API key",
            )

        cached = self._gateway_cache.get(gateway_id)
        if cached and cached.get("api_key_hash"):
            api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()
            if api_key_hash == cached["api_key_hash"] and cached.get("is_active"):
                return cached

        if session is None:
            raise HTTPException(
                status_code=500,
                detail="Database session not available",
            )

        result = await session.execute(
            sa_select(EdgeGateway).where(
                EdgeGateway.gateway_id == gateway_id,
                EdgeGateway.is_active == True,
            )
        )
        gateway = result.scalar_one_or_none()

        if not gateway:
            raise HTTPException(
                status_code=401,
                detail=f"Gateway {gateway_id} not found or inactive",
            )

        api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        if api_key_hash != gateway.api_key_hash:
            raise HTTPException(
                status_code=401,
                detail="Invalid API key",
            )

        gateway_data = {
            "gateway_id": gateway.gateway_id,
            "gateway_name": gateway.gateway_name,
            "tenant_id": str(gateway.tenant_id),
            "plant_id": str(gateway.plant_id) if gateway.plant_id else None,
            "is_active": gateway.is_active,
            "api_key_hash": gateway.api_key_hash,
            "max_batch_size": gateway.max_batch_size,
            "sync_interval_seconds": gateway.sync_interval_seconds,
        }

        self._gateway_cache[gateway_id] = gateway_data
        return gateway_data

    async def _authenticate_mtls(
        self,
        request: Request,
        gateway_id: str,
        session: AsyncSession | None = None,
    ) -> dict[str, Any]:
        ssl_client_cert = request.headers.get("X-SSL-Client-Cert")
        ssl_client_verify = request.headers.get("X-SSL-Client-Verify")

        if not ssl_client_cert or ssl_client_verify != "SUCCESS":
            raise HTTPException(
                status_code=401,
                detail="mTLS certificate not valid",
            )

        cert_serial = self._extract_cert_serial(ssl_client_cert)

        if session is None:
            raise HTTPException(
                status_code=500,
                detail="Database session not available",
            )

        result = await session.execute(
            sa_select(EdgeGateway).where(
                EdgeGateway.gateway_id == gateway_id,
                EdgeGateway.mtls_cert_serial == cert_serial,
                EdgeGateway.is_active == True,
            )
        )
        gateway = result.scalar_one_or_none()

        if not gateway:
            raise HTTPException(
                status_code=401,
                detail=f"Gateway {gateway_id} not found or certificate mismatch",
            )

        return {
            "gateway_id": gateway.gateway_id,
            "gateway_name": gateway.gateway_name,
            "tenant_id": str(gateway.tenant_id),
            "plant_id": str(gateway.plant_id) if gateway.plant_id else None,
            "is_active": gateway.is_active,
            "mtls_cert_serial": cert_serial,
        }

    def _extract_cert_serial(self, cert_pem: str) -> str:
        import base64
        try:
            cert_lines = cert_pem.strip().split("\n")
            cert_data = "".join(line for line in cert_lines if not line.startswith("-----"))
            cert_bytes = base64.b64decode(cert_data)
            return hashlib.sha256(cert_bytes).hexdigest()[:16]
        except Exception:
            return "unknown"

    def invalidate_cache(self, gateway_id: str) -> None:
        self._gateway_cache.pop(gateway_id, None)


edge_auth = EdgeGatewayAuth()


async def require_edge_gateway(
    request: Request,
    api_key: str | None = Security(API_KEY_HEADER),
    session: AsyncSession = None,
) -> dict[str, Any]:
    """FastAPI dependency for Edge Gateway authentication."""
    return await edge_auth.authenticate(request, api_key, session)


def create_mtls_context(
    certfile: str,
    keyfile: str,
    ca_certs: str | None = None,
) -> ssl.SSLContext:
    """Create mTLS SSL context for Edge Gateway server."""
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certfile, keyfile)
    if ca_certs:
        context.load_verify_locations(ca_certs)
    context.verify_mode = ssl.CERT_REQUIRED
    context.check_hostname = False
    return context
