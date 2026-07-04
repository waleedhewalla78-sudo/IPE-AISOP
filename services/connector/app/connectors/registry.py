"""ERP connector registry — unified interface for Odoo (live), SAP/D365 (scaffold)."""

from __future__ import annotations

from enum import Enum
from typing import Any, Protocol


class ERPTYPE(str, Enum):
    ODOO = "odoo"
    SAP = "sap"
    D365 = "d365"


class SyncEngine(Protocol):
    async def sync_all(self) -> dict[str, Any]: ...
    async def sync_manufacturing_orders(self) -> dict[str, Any]: ...
    async def activate(self, mo_ids: list[str], schedule_data: dict[str, Any]) -> dict[str, Any]: ...


class ConnectorRegistry:
    """Factory for ERP connectors based on tenant configuration."""

    def __init__(self, db_session: Any) -> None:
        self.db = db_session
        self._engines: dict[str, Any] = {}

    def get_engine(self, tenant_id: str, erp_type: str | ERPTYPE, config: Any) -> Any:
        """Get or create a sync engine for the tenant's configured ERP."""
        key = f"{tenant_id}:{erp_type}"
        if key in self._engines:
            return self._engines[key]

        et = ERPTYPE(erp_type) if not isinstance(erp_type, ERPTYPE) else erp_type

        if et == ERPTYPE.ODOO:
            # Live Odoo path uses app.odoo.sync_engine.OdooSyncEngine(client, tenant_id, session)
            # constructed by existing sync/activate API handlers — not this factory.
            raise NotImplementedError(
                "Use existing Odoo sync API handlers; registry factory is for SAP/D365 scaffolds"
            )
        elif et == ERPTYPE.SAP:
            from app.connectors.sap.sync_engine import SAPSyncEngine

            engine = SAPSyncEngine(self.db, tenant_id, config)
        elif et == ERPTYPE.D365:
            from app.connectors.d365.sync_engine import D365SyncEngine

            engine = D365SyncEngine(self.db, tenant_id, config)
        else:
            raise ValueError(f"Unsupported ERP type: {erp_type}")

        self._engines[key] = engine
        return engine
