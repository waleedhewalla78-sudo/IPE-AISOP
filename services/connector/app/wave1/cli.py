"""CLI: python -m app.wave1.cli sync --tenant <UUID> --since <ISO>"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path
from uuid import UUID

from app.odoo.client import OdooClient
from app.wave1.base import STAR_TRANS_TENANT
from app.wave1.orchestrator import sync_all_master_data


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="IPE Odoo Wave 1 read-only master sync")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sync_p = sub.add_parser("sync")
    sync_p.add_argument("--tenant", default=str(STAR_TRANS_TENANT))
    sync_p.add_argument("--since", default=None, help="ISO datetime inclusive lower bound")
    args = parser.parse_args(argv)

    if args.cmd != "sync":
        return 2

    client = OdooClient(
        url=os.environ.get("ODOO_URL", "http://localhost:8010"),
        db=os.environ.get("ODOO_DB", "ipe_mock"),
        username=os.environ.get("ODOO_USER", "admin"),
        password=os.environ.get("ODOO_API_KEY", "admin"),
    )
    since = datetime.fromisoformat(args.since) if args.since else None
    report_dir = Path(__file__).resolve().parents[4] / "docs" / "qa"
    print(f"Wave 1 sync tenant={args.tenant} url={client.url}")
    report = sync_all_master_data(UUID(args.tenant), client, since=since, report_dir=report_dir)
    for i, row in enumerate(report.adapters, start=1):
        print(f"  {i}/10 {row.get('entity')}: fetched={row.get('fetched')} upserted={row.get('upserted')} failed={row.get('failed')}")
    print(f"ok={report.ok}")
    return 0 if report.ok else 1


if __name__ == "__main__":
    sys.exit(main())
