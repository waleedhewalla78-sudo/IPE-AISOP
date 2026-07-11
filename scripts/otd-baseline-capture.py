#!/usr/bin/env python3
"""
IPE OTD Baseline Capture — query Odoo mrp.production via XML-RPC.

Usage:
  python scripts/otd-baseline-capture.py \\
    --odoo-url http://localhost:8069 --db star_trans \\
    --user admin --password admin --months 6 \\
    --out otd-baseline.md

Outputs JSON (stdout summary) and optional markdown table file.
Does not invent data: fails clearly if Odoo is unreachable.
"""
from __future__ import annotations

import argparse
import json
import sys
import xmlrpc.client
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Capture OTD baseline from Odoo MRP")
    p.add_argument("--odoo-url", required=True, help="Odoo base URL, e.g. http://host:8069")
    p.add_argument("--db", required=True, help="Odoo database name")
    p.add_argument("--user", required=True, help="Odoo API username")
    p.add_argument("--password", required=True, help="Odoo API password")
    p.add_argument("--months", type=int, default=6, help="Months of history (default 6)")
    p.add_argument("--out", default="", help="Optional markdown output path")
    return p.parse_args()


def connect(url: str, db: str, user: str, password: str):
    common = xmlrpc.client.ServerProxy(f"{url.rstrip('/')}/xmlrpc/2/common")
    uid = common.authenticate(db, user, password, {})
    if not uid:
        raise SystemExit("ERROR: Odoo authentication failed")
    models = xmlrpc.client.ServerProxy(f"{url.rstrip('/')}/xmlrpc/2/object")
    return uid, models


def field_candidates(models, db, uid, password) -> tuple[str, str]:
    """Detect finish/deadline field names for Odoo 17 vs 19."""
    fields = models.execute_kw(
        db, uid, password, "mrp.production", "fields_get", [], {"attributes": ["string"]}
    )
    finish = "date_finished" if "date_finished" in fields else None
    deadline = "date_deadline" if "date_deadline" in fields else None
    if not finish and "date_planned_finished" in fields:
        finish = "date_planned_finished"
    if not deadline:
        if "date_deadline" in fields:
            deadline = "date_deadline"
        elif "date_planned_finished" in fields:
            deadline = "date_planned_finished"
        elif "date_finished" in fields:
            deadline = "date_finished"
    if not finish or not deadline:
        raise SystemExit(f"ERROR: cannot locate finish/deadline fields. Available: {list(fields)[:30]}")
    return finish, deadline


def parse_dt(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value
    # Odoo returns 'YYYY-MM-DD HH:MM:SS'
    try:
        return datetime.strptime(value[:19], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
    except ValueError:
        try:
            return datetime.strptime(value[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            return None


def main() -> int:
    args = parse_args()
    try:
        uid, models = connect(args.odoo_url, args.db, args.user, args.password)
    except Exception as exc:
        print(f"ERROR: cannot connect to Odoo: {exc}", file=sys.stderr)
        return 1

    finish_field, deadline_field = field_candidates(models, args.db, uid, args.password)
    since = datetime.now(timezone.utc) - timedelta(days=30 * args.months)
    since_str = since.strftime("%Y-%m-%d %H:%M:%S")

    domain = [["state", "=", "done"], [finish_field, ">=", since_str]]
    fields = ["name", "product_id", finish_field, deadline_field]
    records = models.execute_kw(
        args.db, uid, args.password, "mrp.production", "search_read",
        [domain], {"fields": fields, "limit": 50000},
    )

    by_month: dict[str, dict[str, int]] = defaultdict(lambda: {"total": 0, "on_time": 0, "late": 0})
    for rec in records:
        finished = parse_dt(rec.get(finish_field))
        deadline = parse_dt(rec.get(deadline_field))
        if not finished:
            continue
        key = finished.strftime("%Y-%m")
        by_month[key]["total"] += 1
        if deadline and finished <= deadline:
            by_month[key]["on_time"] += 1
        else:
            by_month[key]["late"] += 1

    months = []
    total = on_time = late = 0
    for key in sorted(by_month.keys()):
        row = by_month[key]
        pct = round(100.0 * row["on_time"] / row["total"], 1) if row["total"] else 0.0
        months.append({
            "month": key,
            "total_completed": row["total"],
            "on_time": row["on_time"],
            "late": row["late"],
            "otd_pct": pct,
        })
        total += row["total"]
        on_time += row["on_time"]
        late += row["late"]

    overall_pct = round(100.0 * on_time / total, 1) if total else 0.0
    result = {
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "odoo_url": args.odoo_url,
        "database": args.db,
        "months_back": args.months,
        "finish_field": finish_field,
        "deadline_field": deadline_field,
        "months": months,
        "overall": {
            "total_completed": total,
            "on_time": on_time,
            "late": late,
            "otd_pct": overall_pct,
        },
    }
    print(json.dumps(result, indent=2))

    if args.out:
        lines = [
            "# OTD Baseline Capture",
            f"Captured: {result['captured_at']}",
            f"Source: {args.odoo_url} / {args.db}",
            f"Fields: {finish_field} vs {deadline_field}",
            "",
            "| Month | Total MOs Completed | On-Time | Late | OTD % |",
            "|-------|---------------------|---------|------|-------|",
        ]
        for m in months:
            lines.append(
                f"| {m['month']} | {m['total_completed']} | {m['on_time']} | {m['late']} | {m['otd_pct']}% |"
            )
        lines.append(
            f"| **Overall** | {total} | {on_time} | {late} | **{overall_pct}%** |"
        )
        Path(args.out).write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"Wrote markdown: {args.out}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
