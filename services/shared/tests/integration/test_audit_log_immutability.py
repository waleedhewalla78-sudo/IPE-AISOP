"""
Integration test: Verify cdm_audit_log is append-only for the ipe_app role.

Phase 0 migration (001_initial_schema.py) grants SELECT, INSERT, UPDATE on
cdm_audit_log to the ipe_app role, then runs:
    REVOKE UPDATE, DELETE ON cdm_audit_log FROM ipe_app;

This test proves the REVOKE is active by attempting UPDATE/DELETE
as the ipe_app role and asserting PostgreSQL raises
InsufficientPrivilege (or a similar permission error).
"""

import os
from contextlib import suppress

import pytest

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not os.environ.get("IPE_DATABASE_URL"),
        reason="Requires IPE_DATABASE_URL pointing to a RLS-enabled schema",
    ),
]


def _sync_conn():
    import psycopg2

    raw = os.environ["IPE_DATABASE_URL"]
    if raw.startswith("postgresql+asyncpg://"):
        raw = raw.replace("postgresql+asyncpg://", "postgresql://")
    return psycopg2.connect(raw)


def test_update_on_audit_log_raises_insufficient_privilege():
    """Attempt UPDATE on cdm_audit_log as ipe_app — must be denied."""
    import psycopg2

    conn = _sync_conn()
    conn.set_session(autocommit=True)
    cur = conn.cursor()

    try:
        cur.execute("SET ROLE ipe_app")
        cur.execute("UPDATE cdm_audit_log SET action = 'hacked' WHERE id = -1")
        pytest.fail("UPDATE on cdm_audit_log should have been denied")
    except psycopg2.errors.InsufficientPrivilege:
        pass
    except Exception as exc:
        if "permission denied" in str(exc).lower() or "insufficient_privilege" in str(exc).lower():
            return
        pytest.fail(f"Unexpected error (not a permission error): {exc}")
    finally:
        with suppress(Exception):
            cur.execute("RESET ROLE")
        cur.close()
        conn.close()


def test_delete_on_audit_log_raises_insufficient_privilege():
    """Attempt DELETE on cdm_audit_log as ipe_app — must be denied."""
    import psycopg2

    conn = _sync_conn()
    conn.set_session(autocommit=True)
    cur = conn.cursor()

    try:
        cur.execute("SET ROLE ipe_app")
        cur.execute("DELETE FROM cdm_audit_log WHERE id = -1")
        pytest.fail("DELETE on cdm_audit_log should have been denied")
    except psycopg2.errors.InsufficientPrivilege:
        pass
    except Exception as exc:
        if "permission denied" in str(exc).lower() or "insufficient_privilege" in str(exc).lower():
            return
        pytest.fail(f"Unexpected error (not a permission error): {exc}")
    finally:
        with suppress(Exception):
            cur.execute("RESET ROLE")
        cur.close()
        conn.close()
