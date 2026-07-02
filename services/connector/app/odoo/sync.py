"""Backward-compatible alias — use OdooSyncEngine."""

from app.odoo.sync_engine import OdooSyncEngine as SyncAdapter

__all__ = ["SyncAdapter"]
