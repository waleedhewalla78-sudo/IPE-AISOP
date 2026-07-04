"""Multi-ERP connector package (Odoo live; SAP/D365 scaffolds)."""

from app.connectors.registry import ConnectorRegistry, ERPTYPE

__all__ = ["ConnectorRegistry", "ERPTYPE"]
