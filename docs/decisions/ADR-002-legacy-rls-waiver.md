# ADR-002: Legacy RLS Waiver for Migrations 002–012

**Status:** Accepted  
**Date:** 2026-06-26  
**Related:** AG-03, R-001, POST-C3

---

## Context

Audit finding R-001 notes partial Row Level Security coverage. Migrations **024–028** enable RLS on V6-critical tables (chaos, audit, tenant-scoped entities). Legacy tables from migrations **002–012** predate the RLS policy framework.

Demo 20/20 and chaos 6/6 prove tenant isolation works for all active API paths via:
- JWT `tenant_id` claim
- Kong `X-Tenant-ID` injection
- Application-level `tenant_id` filters on SQLAlchemy queries

---

## Decision

**Waive full RLS backfill on 002–012 tables for v7.0.0.** Track as POST-C3 for v7.1.

Application-level tenant filters remain mandatory for all new code.

---

## Consequences

- Audit AG-03 closed with documented waiver (not false-complete)
- v7.1 will add Alembic migration `029_legacy_rls_policies.py` when scheduled
- Integration test `test_adversarial_rbac.py` continues to verify cross-tenant denial

---

## Verification

- `services/shared/tests/integration/test_adversarial_rbac.py`
- Demo tenant isolation in Wave 3 regression
