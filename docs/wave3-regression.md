# Wave 3 Regression — v6.1.0 Gate

**Date:** 2026-06-26  
**Scope:** W3-01 (TLS runbook), W3-02 (JWT runbook), W3-03 (SEC-05 migration 028), live demo + chaos  
**Migration applied:** `027 → 028` via `docker compose run --rm migrate`

---

## W3-01 — TLS Runbook ✅

| Check | Result |
|-------|--------|
| `docs/runbooks/tls-internal.md` | ✅ |
| Termination, passthrough, cert gen/rotation, Kong, verify, rollback | ✅ |
| C-03 reference | ✅ |

---

## W3-02 — JWT Rotation Runbook ✅

| Check | Result |
|-------|--------|
| `docs/runbooks/jwt-rotation.md` | ✅ |
| Dual-key window, Kong update, restart order, rollback | ✅ |
| C-04 reference | ✅ |

---

## W3-03 — SEC-05 Migration ✅

| Check | Result |
|-------|--------|
| `migrations/versions/028_sec05_password_hash_backfill.py` | ✅ |
| `{SHA-256}` + SHA256 hex backfill | ✅ |
| Reversible downgrade | ✅ |
| Alembic live upgrade | ✅ `027 → 028` |
| `dpe-svc/tests/test_auth.py` | **4/4 PASS** |

---

## W3-04 — Live Demo 20/20 ✅

| Run | Report | Result |
|-----|--------|--------|
| **Wave 3 live** | `docs/demo-run-report-wave3-live.txt` | **20/20 PASS** (2026-06-26 15:10) |
| Post-chaos (C6) | `docs/demo-run-report-post-chaos.txt` | **20/20 PASS** (2026-06-26 15:15) |

Post-migration **028** + Wave 3 auth changes — full demo green on live stack.

---

## W3-04 — Chaos C1–C6 ✅

| Scenario | Evidence | Result |
|----------|----------|--------|
| C1 nlp kill | `docs/chaos/C1-nlp-kill.md` | **PASS** |
| C2 alert kill | `docs/chaos/C2-alert-kill.md` | **PASS** |
| C3 Kafka pause + approve | `docs/chaos/C3-kafka-pause-approve.md` | **PASS** |
| C4 Kafka drain | `docs/chaos/C4-kafka-drain.md` | **PASS** |
| C5 PG connections | `docs/chaos/C5-pg-connections.md` | **PASS** |
| C6 post-chaos 20/20 | `docs/chaos/C6-post-chaos-regression.md` | **PASS** |

**Overall: 6/6** (2026-06-26 15:12–15:15)

---

## Acceptance Criteria — v6.1.0

| Criterion | Status |
|-----------|--------|
| `docs/runbooks/tls-internal.md` | ✅ |
| `docs/runbooks/jwt-rotation.md` | ✅ |
| Alembic migration reversible + applied | ✅ |
| Demo 20/20 | ✅ **live** |
| Chaos C1–C6 | ✅ **live** |
| Git tag `v6.1.0` | ✅ |

---

## Overall Verdict

**v6.1.0 RELEASE GATE: PASS**

Estimated audit score: **~95/100** (C-03, C-04, SEC-05 closed at documentation + migration level).
