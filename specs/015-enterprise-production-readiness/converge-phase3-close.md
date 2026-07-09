# Speckit Converge — Spec 015 Phase 3 Close-Out

**Date**: 2026-07-05  
**Command**: `/speckit.converge`  
**Constitution**: v1.2.2 (8 principles)  
**Target tag**: `v9.4.0-p3` — **NOT APPLIED** (Docker Desktop unavailable; Gates 9–11 not re-run)

---

## 1. Executive summary

| Stream | Task | Code status | Runtime status |
|--------|------|-------------|----------------|
| 1 | T169 Kafka-optional health | ✅ Complete | ⬜ Compose rebuild pending Docker |
| 1 | T164 K8s migrate/seed | ✅ Script ready | ⬜ Blocked — Docker/kind down |
| 2 | T165 Gate 9 HPA | ✅ Script + values-gate9.yaml | ⬜ Blocked — no cluster |
| 2 | T166 Gate 11 R1 K8s | ✅ verify-gate11.ps1 | ⬜ Blocked — no ingress |
| 3 | T157 Tag v9.4.0-p3 | ⬜ | **Blocked** — Constitution VIII |

**Prior session evidence (2026-07-04/05):** Gates 6, 7, 8, 10 previously PASS when kind was healthy. **This session:** Docker Desktop API returns 500 — cannot re-verify or complete Gates 9–11.

---

## 2. Gate matrix (final target vs current)

| Gate | Requirement | Evidence path | Status |
|------|-------------|---------------|--------|
| 6 | Helm lint/template | `scripts/k8s/verify-gate6.ps1` | ✅ PASS (2026-07-04) |
| 7 | kind deploy + health | `scripts/k8s/verify-k8s.ps1` | ✅ PASS (2026-07-05, prior) |
| 8 | Compose–K8s parity | `evidence/gate8-parity.txt` + parity script | ✅ PASS (2026-07-05 prior); re-run pending |
| 9 | HPA smoke | `evidence/gate9-hpa.txt` | ⬜ **PENDING** |
| 10 | ERP scaffolds | `tests/test_erp_scaffolds.py` | ✅ PASS |
| 11 | R1 demo on K8s | `evidence/gate11-r1-k8s.txt` | ⬜ **PENDING** |

**Tag policy:** `git tag v9.4.0-p3` ONLY after Gates 9 and 11 have fresh evidence files with PASS.

---

## 3. Work completed this converge run

### T169 — Release 1 health (Constitution VII, V)

| File | Change |
|------|--------|
| `services/shared/ipe_shared/health/probes.py` | `kafka_required()`, skip Kafka/Vault for `release1` |
| `services/shared/ipe_shared/health/endpoints.py` | `/ready` accepts skipped optional deps |
| `infrastructure/docker/docker-compose.release1.yml` | `IPE_KAFKA_BOOTSTRAP_SERVERS=""`, `IPE_KAFKA_ENABLED=false` on connector |
| `helm/ipe/values-dev.yaml` | `IPE_KAFKA_BOOTSTRAP_SERVERS=""` (prior) |
| `services/shared/tests/test_health_probes_release1.py` | 5 unit tests — all PASS |

Evidence: `evidence/t169-health-probes.txt`

### T164 — K8s DB migrate (prepared)

Script: `scripts/k8s/migrate-k8s-db.ps1`  
Run when Docker/kind is up:

```powershell
cd E:\AISOP\ipe
.\scripts\k8s\migrate-k8s-db.ps1 -Seed
.\scripts\k8s\verify-gate8.ps1
```

### T165 — Gate 9 (prepared)

- `helm/ipe/values-gate9.yaml` — HPA min=2 max=4 on dpe/fea/cap
- `scripts/k8s/verify-gate9.ps1`

```powershell
helm upgrade ipe ./helm/ipe -n ipe -f ./helm/ipe/values-gate9.yaml --wait
.\scripts\k8s\verify-gate9.ps1
```

### T166 — Gate 11 (prepared)

- `scripts/k8s/verify-gate11.ps1` wraps `run-release1-integration-demo.ps1` with `BaseUrl=http://localhost/api/v1`

### Constitution v1.2.2

- Principle IV: R1 Kafka optional env documented
- Principle VIII: Gate 8 PASS noted; 9/11 still required for tag

---

## 4. Constitution compliance (post-change)

| Principle | Status | Notes |
|-----------|--------|-------|
| I RLS | ✅ | No new migrations in this run |
| II Auth | ✅ | No new endpoints |
| III Tests | ✅ | T169: 5 probe tests PASS |
| IV Events | ✅ | Kafka skipped in R1 profile |
| V Architecture | ✅ | `/ready` updated for K8s probes |
| VI Observability | ⬜ | Gate 9 HPA evidence pending |
| VII Customer-first | ✅ | R1 compose-first; Kafka optional |
| VIII Gate verification | 🔴 | **Tag blocked** — Gates 9, 11 open |

---

## 5. Phase 3 → 100% checklist (operator runbook)

Execute **in order** after starting Docker Desktop:

```powershell
cd E:\AISOP\ipe

# 1. T169 verify compose
docker compose -f infrastructure/docker/docker-compose.release1.yml up -d --build
# all R1 services healthy

# 2. T164 + Gate 8
kind create cluster --name ipe-dev  # if missing
.\scripts\k8s\deploy-kind.ps1      # or helm-install-gate7.ps1
.\scripts\k8s\migrate-k8s-db.ps1 -Seed
.\scripts\k8s\verify-gate8.ps1

# 3. T165 Gate 9
helm upgrade ipe ./helm/ipe -n ipe -f ./helm/ipe/values-gate9.yaml --wait
.\scripts\k8s\verify-gate9.ps1

# 4. T166 Gate 11
.\scripts\k8s\verify-gate11.ps1

# 5. T157 Tag (only if all evidence PASS)
git add -A && git status
git tag -a v9.4.0-p3 -m "Spec 015 Phase 3 complete: Gates 6-11 PASS"
git log --oneline -5
git tag -l "v9.4*"
```

---

## 6. Phase 4 preparation (T170–T179) — issue templates

Create after `v9.4.0-p3` tag with label `enterprise-phase-4`:

| Task | Title | FR |
|------|-------|-----|
| T170 | Tenant self-service API | FR-015-40 |
| T171 | Stripe integration scaffold | FR-015-41 |
| T172 | Terraform module ipe-saas | FR-015-46 |
| T173 | Python/JS SDKs | FR-015-43 |
| T174 | GitBook knowledge base | FR-015-44 |
| T175 | Mobile-responsive web | FR-015-47 |
| T176 | Customer portal signup/provision | FR-015-40 |
| T177 | Admin portal tenant CRUD | FR-015-45 |
| T178 | Release pipeline GH Actions | FR-015-48 |
| T179 | Phase 4 speckit artifact refresh | spec/plan/tasks |

```powershell
gh label create enterprise-phase-4 --description "Enterprise Phase 4 GTM/SaaS"
gh issue create --title "T170: Tenant self-service API" --label enterprise-phase-4 --body "FR-015-40. POST/GET /api/v1/tenants. RLS required."
# ... repeat T171–T179
```

Existing: [#25](https://github.com/waleedhewalla78-sudo/IPE-AISOP/issues/25) T172, [#26](https://github.com/waleedhewalla78-sudo/IPE-AISOP/issues/26) T173 (renumber in backlog grooming).

---

## 7. Phase 5 draft backlog (T200a–T209a)

| ID | Item | Stream | v8 doc ref |
|----|------|--------|------------|
| T200a | SOC 2 Type II evidence | A | Gap Audit |
| T201a | GDPR DSAR automation | A | FR-015-51 |
| T202a | WCAG 2.1 AA (axe-core) | A | FR-015-52 |
| T203a | S&OP + demand-svc | B | v8 U2–U3 |
| T204a | Copilot production guardrails | B | v8 U1 |
| T205a | Live SAP S/4 connector | C | FR-015-57 |
| T206a | Live D365 connector | C | FR-015-58 |
| T207a | Multi-site supply network | C | v8 U4 |
| T208a | Terraform HA multi-AZ | C | Phase 5 |
| T209a | Amend spec FR-015-50–59 | — | spec maintenance |

**Not started** — depends on Phase 4 GTM baseline.

---

## 8. Star Trans R1 (T163)

**Business-blocked:** SOW signature + Odoo staging. No engineering action. See `docs/customer/star-trans/SOW-STATUS.md`.

---

## 9. Remaining tasks appended (convergence)

| ID | Task | Priority | Status |
|----|------|----------|--------|
| T171b | Re-run Gate 8 after Docker restart | P0 | ⬜ |
| T172b | Execute Gate 9 with values-gate9.yaml | P0 | ⬜ |
| T173b | Execute Gate 11 verify-gate11.ps1 | P0 | ⬜ |
| T174b | Commit Phase 3 close-out changes | P0 | ⬜ |
| T175b | Tag v9.4.0-p3 | P0 | ⬜ Blocked |
| T176b | Close GitHub #15–#18 after gates | P2 | ⬜ |
| T177b | Create T170–T179 Phase 4 issues | P2 | ⬜ After tag |
| T178b | Sync ENTERPRISE-PROGRAM-STATUS.md | P2 | ⬜ |

---

## 10. v8 SAP Gap Analysis alignment

Tier 1 (Copilot, demand sensing, scenario) → Phase 5 Stream B (FR-015-54–55).  
Does **not** block Phase 3 tag or Star Trans R1 compose go-live (Constitution VII).

---

*Converge document v1.0 — Phase 3 close-out blocked on Docker Desktop availability for Gates 9–11.*
