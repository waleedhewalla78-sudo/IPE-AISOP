"""Odoo Accounting integration — SCAFFOLD / MOCK ONLY.

Live Odoo Accounting (journal entries, AP/AR aging, cash position) is gated by
**PH1-02 (live Odoo staging) — OPEN**. This module MUST NOT be presented as a
live integration. It exposes the interface A11/A14 will consume and returns
clearly-labelled mock figures so downstream agents can be developed and tested
without faking a live feed.

When PH1-02 clears, replace ``_MockAccountingSource`` with an XML-RPC-backed
implementation behind the same ``AccountingSource`` protocol.
"""

from __future__ import annotations

from typing import Any, Protocol


class AccountingSource(Protocol):
    """Interface for an accounting data provider (mock or live Odoo)."""

    def ap_ar_aging(self, tenant_id: str) -> dict[str, Any]: ...

    def cash_position(self, tenant_id: str) -> dict[str, Any]: ...


class _MockAccountingSource:
    """Deterministic mock — NOT connected to any ERP."""

    mode = "mock"

    def ap_ar_aging(self, tenant_id: str) -> dict[str, Any]:
        return {
            "source": "mock",
            "live": False,
            "blocker": "PH1-02 live Odoo Accounting OPEN",
            "accounts_receivable": {
                "current": 512_000.0,
                "1_30": 180_000.0,
                "31_60": 64_000.0,
                "61_90": 21_000.0,
                "over_90": 8_000.0,
            },
            "accounts_payable": {
                "current": 288_000.0,
                "1_30": 96_000.0,
                "31_60": 12_000.0,
            },
        }

    def cash_position(self, tenant_id: str) -> dict[str, Any]:
        return {
            "source": "mock",
            "live": False,
            "blocker": "PH1-02 live Odoo Accounting OPEN",
            "cash_reserves": 1_240_000.0,
            "committed_po_value": 612_000.0,
            "as_of": "2026-07-16",
        }


class OdooAccountingConnector:
    """Facade returning accounting data with an explicit live/mock flag.

    Defaults to the mock source. Pass a live ``AccountingSource`` only once
    PH1-02 is cleared and an XML-RPC implementation exists.
    """

    def __init__(self, source: AccountingSource | None = None) -> None:
        self._source: AccountingSource = source or _MockAccountingSource()

    @property
    def is_live(self) -> bool:
        return getattr(self._source, "mode", "mock") == "live"

    def ap_ar_aging(self, tenant_id: str) -> dict[str, Any]:
        data = self._source.ap_ar_aging(tenant_id)
        data.setdefault("live", self.is_live)
        return data

    def cash_position(self, tenant_id: str) -> dict[str, Any]:
        data = self._source.cash_position(tenant_id)
        data.setdefault("live", self.is_live)
        return data

    def status(self) -> dict[str, Any]:
        return {
            "integration": "odoo_accounting",
            "live": self.is_live,
            "mode": "mock" if not self.is_live else "live",
            "blocker": None if self.is_live else "PH1-02 live Odoo Accounting OPEN — do not fake",
        }
