#!/usr/bin/env python3
"""RLS Audit Script — TASK-P1-008

Connects to PostgreSQL and verifies that every table with a tenant_id column
has Row-Level Security enabled and a tenant_isolation policy attached.

Exit codes:
    0 — all checks pass
    1 — one or more violations found
    2 — connection / query error

Usage:
    python scripts/audit-rls.py
    DATABASE_URL=postgresql://... python scripts/audit-rls.py
"""

import os
import sys

import psycopg2


DEFAULT_DSN = "postgresql://ipe:ipe_dev_pass@localhost:5432/ipe_dev"

BANNER = "=" * 72


def get_dsn() -> str:
    dsn = os.environ.get("DATABASE_URL") or os.environ.get("IPE_DATABASE_URL_SYNC")
    if not dsn:
        dsn = DEFAULT_DSN
    return dsn


def fetch_tables_with_tenant_id(cur) -> list[str]:
    cur.execute(
        """
        SELECT table_name
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND column_name = 'tenant_id'
        ORDER BY table_name
        """
    )
    return [row[0] for row in cur.fetchall()]


def fetch_rls_status(cur, tables: list[str]) -> dict:
    result = {}
    for table in tables:
        cur.execute(
            """
            SELECT relrowsecurity
            FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = 'public'
              AND c.relname = %s
            """,
            (table,),
        )
        row = cur.fetchone()
        result[table] = bool(row[0]) if row else False
    return result


def fetch_policies(cur, tables: list[str]) -> dict[str, list[str]]:
    result = {}
    for table in tables:
        cur.execute(
            """
            SELECT polname
            FROM pg_policy p
            JOIN pg_class c ON c.oid = p.polrelid
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = 'public'
              AND c.relname = %s
            """,
            (table,),
        )
        result[table] = [row[0] for row in cur.fetchall()]
    return result


def audit(dsn: str) -> bool:
    violations = 0

    conn = psycopg2.connect(dsn)
    conn.autocommit = True
    try:
        cur = conn.cursor()

        tables = fetch_tables_with_tenant_id(cur)
        if not tables:
            print("No tables with tenant_id found in the public schema.")
            return True

        rls_status = fetch_rls_status(cur, tables)
        policies = fetch_policies(cur, tables)

        print(BANNER)
        print(" RLS AUDIT REPORT")
        print(BANNER)
        print(f"\nTotal tables with tenant_id: {len(tables)}\n")

        rls_enabled = [t for t in tables if rls_status.get(t)]
        rls_missing = [t for t in tables if not rls_status.get(t)]

        print(f"--- Tables with RLS enabled ({len(rls_enabled)}) ---")
        for t in rls_enabled:
            pols = policies.get(t, [])
            pol_str = ", ".join(pols) if pols else "(none)"
            marker = "\u2713"
            print(f"  {marker} {t}: policies=[{pol_str}]")

        print()
        print(f"--- Tables with tenant_id but WITHOUT RLS ({len(rls_missing)}) ---")
        for t in rls_missing:
            marker = "\u2717"
            print(f"  {marker} {t}")
            violations += 1

        no_policy = [
            t for t in rls_enabled if "tenant_isolation" not in policies.get(t, [])
        ]
        print()
        print(
            f"--- Tables with RLS but missing tenant_isolation policy ({len(no_policy)}) ---"
        )
        for t in no_policy:
            pols = policies.get(t, [])
            pol_str = ", ".join(pols) if pols else "(none)"
            marker = "\u2717"
            print(f"  {marker} {t}: existing policies=[{pol_str}]")
            violations += 1

        print()
        print(BANNER)
        if violations == 0:
            print(" RESULT: All checks passed.")
        else:
            print(f" RESULT: {violations} violation(s) found!")
        print(BANNER)

        return violations == 0
    finally:
        conn.close()


def main() -> None:
    dsn = get_dsn()
    try:
        ok = audit(dsn)
    except psycopg2.OperationalError as exc:
        print(f"ERROR: Could not connect to database: {exc}", file=sys.stderr)
        sys.exit(2)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(2)

    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()