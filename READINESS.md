# IPE Platform — Deployment Readiness

**Version**: v6.0.1 (post-audit fixes, REL-PROD active)  
**Published**: 2026-06-26  
**Supersedes**: v6.0.0 (004 complete) + v1.0.0

---

## Overall Score: 97/100 (Speckit) · ~82/100 (Audit est.)

| Metric | Value |
|--------|-------|
| **Live demo** | **20/20** stable (`docs/demo-run-report-v6.txt`, `docs/full-data-demo-report.txt`) |
| **Git** | 5+ commits; tags **v1.0.0** (`4efb8de`), **v6.0.0** (`a203e68`), **v6.0.1** (post-rebuild) |
| **T055 / v6.0.0 tag** | ✅ Complete — user approved, tagged on `a203e68` |
| **Audit fixes (fea0705)** | C-01, C-02 verified, BUG-02, BUG-03 — committed; rebuild required for live stack |
| **Phase** | **REL-PROD** — active critical path to 100/100 |
| **Production 100/100** | Requires k6 200 VU + Chaos evidence + coverage 60% + ops tooling (Phase 3) |

| Dimension | Score | Notes |
|-----------|-------|-------|
| Product completeness | 98 | V5 loop + V6 tariff/CPM/maintenance/chaos/war-room |
| Testing | 92 | 870+ backend tests; demo 20/20; integration 41 pass / 8 fail / 14 skip (live) |
| Security | 76 | RBAC + RLS; JWT demo auth; Keycloak live BLOCKED (C-007) |
| Operations | 88 | Launch checklist, CPM Prometheus; Loki/Grafana pending (REL-PROD) |
| Documentation | 95 | Speckit 005 converge; runbooks C-03/C-04 pending |

See `specs/005-ipe-program-status/converge.md` and `specs/004-ai-first-v6/clarify-v6.md`.

---

## Git Lineage (oldest → newest)

| Commit | Description | Tag |
|--------|-------------|-----|
| `4efb8de` | Release v1.0.0 | v1.0.0 |
| `512a515` | feat(v6): speckit release track | — |
| `a203e68` | Release v6.0.0: 20/20 live demo gate | **v6.0.0** |
| `fea0705` | v6.0.0-post: audit fixes C-01/C-02/BUG-02/BUG-03 | — |
| `0043203` | Spec-Kit converge + full-cycle demo evidence | — |

**Audit fixes committed in `fea0705`**: mat-svc C-01 (`rule_based_atp`), cap-svc BUG-02 (MDR fail-closed 503), BUG-03 (optimistic lock 409).

---

## Phase Completion

| Phase | Scope | Status |
|-------|-------|--------|
| 0 — Git + P0 fixes | GIT-01, C-01–C-02, BUG-02–03 | ✅ Complete |
| 1 — Demo 20/20 + tag | T016–T022, T055 / v6.0.0 | ✅ Complete |
| 2 — Audit criticals (code) | fea0705 | ✅ Complete |
| 2 — Audit remainder | C-03 TLS, C-04 JWT, SEC-05 password_hash | ⬜ Open |
| 3 — REL-PROD | k6, Chaos, coverage 60%, Loki/Grafana | ⬜ **Active** |
| 4–7 | Keycloak, Stripe, hardening, BRD | ⬜ Future |

---

## V6.0 Deliverables (004) — Live Proven

| Phase | Exit Gate | Demo Checkpoint | Live |
|-------|-----------|-----------------|------|
| V6-R1 Activity-Based Planning | ≥8% activity-cost delta | 17 | ✅ |
| V6-R2 Tariff & Landed Cost | Shock + substitute draft | 18 | ✅ |
| V6-R3 Visual CPM | p95 cascade <2s | 19 | ✅ |
| V6-R4 Predictive Maintenance | RUL → block published | 20 | ✅ |
| V6-R5 Cost of Chaos + War Room | ≥3 chaos categories; recovery top-3 | 20 | ✅ |

---

## Risk Register (Summary)

### P0 — Blocks v6.0.0 tag (all closed)

| ID | Issue | Status | Evidence |
|----|-------|--------|----------|
| GIT-01 | Zero git commits | ✅ Closed | 5 commits, 1,111 tracked files |
| T016 | Copilot 503 | ✅ Closed | nlp-svc fallback; CP10–11 pass |
| T017 | CP15 persist after approve | ✅ Closed | T021/T022; CP15 pass |
| T018 | Tariff shock 500 | ✅ Closed | BillOfMaterial join; CP18 pass |
| T019 | Chaos/maintenance 500 | ✅ Closed | alert-svc init + seed; CP20 pass |
| BUG-01 | ERP sync silent drop | ✅ Closed | `a203e68` |

### P1 — Blocks production deployment

| ID | Issue | Status |
|----|-------|--------|
| BUG-02 | MDR gate fail-open | ✅ Closed (fea0705) — rebuild to live |
| BUG-03 | Approve race (no version guard) | ✅ Closed (fea0705) |
| C-01 | check-availability → rule_based_atp | ✅ Closed (fea0705) |
| C-02 | Double /api/v1 prefix on CTP | ✅ Verified no change needed |
| R-01 | Coverage at 40% | ⬜ Open — REL-PROD 3C |
| SEC-01 | No TLS between internal services | ⬜ Open — C-03 runbook + prod mesh |

### P2 — Post-tag remediation

| ID | Issue | Status |
|----|-------|--------|
| C-03 | TLS termination not verified | ⬜ Open |
| C-04 | JWT rotation undocumented | ⬜ Open |
| SEC-05 | password_hash column | ⬜ Open |
| R-08 | No log aggregation | ⬜ Open — REL-PROD 3D |
| INT-01 | test_capacity_schedule live E2E | ⬜ Monitor |
| DOC-01 | PRD scope drift | ⬜ Open |

### Phase 3 risks (new)

| Risk | Mitigation |
|------|------------|
| k6 performance regression | Profile slow queries; tune container limits |
| Chaos data loss | Verify CDM persist + Kafka outbox on C3/C4 |
| Coverage measurement gaps | pytest-cov per service before raising threshold |

---

## Blocked Items

| Item | ID | Reason |
|------|-----|--------|
| Keycloak live IdP / SAML / SCIM | C-007 | Demo uses JWT; no Azure AD/Okta sandbox |

---

## Residual Risks (97 → 100)

- **k6 200 VU** — `tests/performance/k6/`; not executed with evidence yet
- **Chaos engineering** — 6 scenarios; evidence pending under `docs/chaos/`
- **Coverage 40% → 60%** — audit R-01; cap-svc, mat-svc, dpe-svc priority
- **Loki + Grafana** — ops readiness gap
- Keycloak SAML/SCIM (C-007) — BLOCKED

---

## Evidence

- **Demo 20/20**: `docs/demo-run-report-v6.txt`, `docs/full-data-demo-report.txt`
- **Launch verification**: `scripts/launch-verify.ps1`
- **Demo script**: `scripts/run-full-demo.ps1`
- **Converge matrix**: `specs/005-ipe-program-status/converge.md`
- **Integration (live)**: `docs/integration-report-live.txt`

---

## Canonical Repository Layout

| Path | Role |
|------|------|
| `E:/AISOP/ipe/` | **Canonical monorepo** |
| `E:/AISOP/services/` | Orphan duplicate — do not deploy |
| `E:/AISOP/ipe/.specify/` | Spec Kit config (program feature: 005) |

---

## End User Guide Alignment

Routes: Control Tower (+ Tariff panel), Schedule (CPM + export), `/tariff`, `/cost-of-chaos`, War Room (recovery plan), Resolution Center, Copilot, Executive, Shop Floor, MDR, AI Trust, SCN Portal.

**Login**: http://localhost:8082 — `Ahmed@nour` / `admin` (demo tenant)

---

## Current Critical Path → Phase 3 REL-PROD

1. Rebuild cap-svc + mat-svc (audit fixes live) → verify 20/20
2. k6 smoke + 10 VU + 200 VU baselines
3. Chaos scenarios C1–C6
4. Coverage 40% → 60% (cap-svc, mat-svc, dpe-svc)
5. Loki + Grafana minimum viable monitoring
6. C-03/C-04 runbooks + SEC-05 migration → tag **v6.1.0**

**Audit trajectory**: ~82 (v6.0.1) → ~90+ (v6.1.0) → 100/100 (Phase 4+)
