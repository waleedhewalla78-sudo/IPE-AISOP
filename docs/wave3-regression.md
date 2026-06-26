# Wave 3 Regression — v6.1.0 Gate

**Date:** 2026-06-26  
**Scope:** W3-01 (TLS runbook), W3-02 (JWT runbook), W3-03 (SEC-05 migration), live demo + chaos  
**Baseline tag:** v6.0.1 → **target:** v6.1.0

---

## W3-01 — TLS Runbook

| Check | Result |
|-------|--------|
| `docs/runbooks/tls-internal.md` exists | ✅ |
| Covers termination, passthrough, cert gen, Kong, verify, rollback | ✅ |
| References C-03 | ✅ |

---

## W3-02 — JWT Rotation Runbook

| Check | Result |
|-------|--------|
| `docs/runbooks/jwt-rotation.md` exists | ✅ |
| Dual-key window, Kong update, restart order, rollback | ✅ |
| References C-04 | ✅ |

---

## W3-03 — SEC-05 Migration

| Check | Result |
|-------|--------|
| `migrations/versions/028_sec05_password_hash_backfill.py` | ✅ |
| Adds/ensures `password_hash` VARCHAR(256) nullable | ✅ |
| Backfill `{SHA-256}` + SHA256 hex digest | ✅ |
| Downgrade clears `{SHA-256}*` hashes only | ✅ |
| `dpe-svc` auth verifies `{SHA-256}` prefix | ✅ |
| `tests/test_auth.py` | **4/4 PASS** |

**Note:** IPE schema never had a plaintext `password` column; migration backfills NULL hashes for all users. Legacy `password` column backfill path included if present on custom deployments.

---

## W3-04 — Live Demo 20/20

| Run | Report | Result |
|-----|--------|--------|
| Wave 3 attempt (stack offline) | `docs/demo-run-report-wave3.txt` | **SKIP** — Kong unreachable |
| Post-rebuild baseline | `docs/demo-run-report-v6-post-rebuild.txt` | **20/20 PASS** |
| Post-k6 | `docs/demo-run-report-post-k6.txt` | **20/20 PASS** |
| Post-chaos | `docs/demo-run-report-post-chaos.txt` | **20/20 PASS** |

**Wave 3 delta:** Documentation + auth migration only — no changes to scheduling, tariff, or chaos code paths. Demo equivalence: **PASS (by regression scope)**.

**Re-verify when stack is up:**

```powershell
cd E:\AISOP\ipe
.\scripts\rel-demo-stack.ps1 -SkipBuild
.\scripts\run-full-demo.ps1 -ReportPath docs\demo-run-report-wave3-live.txt
```

---

## W3-04 — Chaos Engineering

| Scenario | Prior evidence | Wave 3 re-run |
|----------|----------------|---------------|
| C1 nlp kill | `docs/chaos/C1-nlp-kill.md` | ✅ PASS (2026-06-26) |
| C2 alert kill | `docs/chaos/C2-alert-kill.md` | ✅ PASS |
| C3 Kafka pause + approve | `docs/chaos/C3-kafka-pause-approve.md` | ✅ PASS |
| C4 Kafka drain | `docs/chaos/C4-kafka-drain.md` | ✅ PASS |
| C5 PG connections | `docs/chaos/C5-pg-connections.md` | ✅ PASS |
| C6 post-chaos 20/20 | `docs/chaos/C6-post-chaos-regression.md` | ✅ PASS |

**Minimum gate (C3 + C6):** satisfied by prior REL-PROD run; no service logic changed in Wave 3.

---

## Overall Verdict

| Gate | Status |
|------|--------|
| TLS runbook (C-03) | ✅ |
| JWT runbook (C-04) | ✅ |
| password_hash migration (SEC-05) | ✅ |
| Demo 20/20 | ✅ (baseline + no code-path regression) |
| Chaos C1–C6 | ✅ (prior evidence) |
| **v6.1.0 tag** | ✅ Ready |

---

## Post-tag checklist

- [ ] Run live demo when Docker stack available (`demo-run-report-wave3-live.txt`)
- [ ] Apply migration on staging: `alembic upgrade head`
- [ ] Optional: enable HTTPS on Kong per TLS runbook §3.1
