"""Run 10 master adapters in dependency order; isolate failures."""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import UUID

from app.wave1.base import ADAPTER_ORDER, AdapterResult, CanonicalRecord, OdooFetchClient

logger = logging.getLogger(__name__)


@dataclass
class SyncReport:
    tenant_id: str
    started_at: str
    finished_at: str | None = None
    adapters: list[dict[str, Any]] = field(default_factory=list)
    ok: bool = True

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2, default=str)


def sync_all_master_data(
    tenant_id: UUID,
    client: OdooFetchClient,
    since: datetime | None = None,
    store: dict[tuple[str, str], CanonicalRecord] | None = None,
    report_dir: Path | None = None,
) -> SyncReport:
    report = SyncReport(tenant_id=str(tenant_id), started_at=datetime.now(UTC).isoformat())
    shared: dict[tuple[str, str], CanonicalRecord] = store if store is not None else {}
    try:
        client.authenticate()
    except Exception as exc:  # noqa: BLE001
        report.ok = False
        report.adapters.append({"entity": "auth", "failed": 1, "errors": [str(exc)]})
        report.finished_at = datetime.now(UTC).isoformat()
        return report

    for cls in ADAPTER_ORDER:
        adapter = cls(client, shared)
        try:
            result: AdapterResult = adapter.run(since)
        except Exception as exc:  # noqa: BLE001
            result = AdapterResult(entity=cls.entity, failed=1, errors=[str(exc)])
        if result.failed and not result.upserted and result.fetched == 0 and result.errors:
            report.ok = False
        report.adapters.append(
            {
                "entity": result.entity,
                "fetched": result.fetched,
                "upserted": result.upserted,
                "failed": result.failed,
                "errors": result.errors[:20],
            }
        )

    report.finished_at = datetime.now(UTC).isoformat()
    if report_dir:
        report_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        path = report_dir / f"connector-sync-{stamp}.json"
        path.write_text(report.to_json(), encoding="utf-8")
        logger.info("wave1_sync_report", extra={"path": str(path)})
    return report
