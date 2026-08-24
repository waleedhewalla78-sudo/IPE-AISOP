"""Nightly-style verifier: python -m app.verify_audit_integrity (from nlp-svc)."""

from __future__ import annotations

import os
import sys

from app.audit_middleware import verify_integrity


def main() -> int:
    dsn = os.environ.get("IPE_DATABASE_URL_SYNC")
    if not dsn:
        print("IPE_DATABASE_URL_SYNC not set; skip")
        return 0
    try:
        import psycopg2
    except ImportError:
        print("psycopg2 missing; skip")
        return 0
    conn = psycopg2.connect(dsn)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT query_id, query_text, response_text, created_at_epoch, tenant_id, integrity_hash
        FROM cdm_copilot_audit
        WHERE created_at > now() - interval '24 hours'
        """
    )
    mismatches = 0
    for row in cur.fetchall():
        rec = {
            "query_id": row[0],
            "query_text": row[1],
            "response_text": row[2],
            "created_at_epoch": row[3],
            "tenant_id": row[4],
            "integrity_hash": row[5],
        }
        if rec["integrity_hash"] and not verify_integrity(rec):
            mismatches += 1
            print(f"MISMATCH {rec['query_id']}")
    conn.close()
    print(f"mismatches={mismatches}")
    return 1 if mismatches else 0


if __name__ == "__main__":
    sys.exit(main())
