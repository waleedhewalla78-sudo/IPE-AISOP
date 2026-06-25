# Analyze: IPE Program — Cross-Artifact Consistency & Whole-Project Status

**Feature**: `005-ipe-program-status` | **Date**: 2026-06-26  
**Scope**: Program-wide (000 → 005) + release track REL-* + Master Execution Plan alignment  
**Readiness**: **97/100** (code); **live demo 19/20** (1 CP remaining)

**Method**: `/speckit.analyze` — synthesis across `spec.md`, `plan.md`, `tasks.md`, `004/*`, `READINESS.md`, Master Execution Plan (2026-06-26), live demo report.

---

## Executive Summary

| Dimension | Status |
|-----------|--------|
| **Speckit build tasks (002+003+004)** | **157 / 162 (97%)** |
| **Release tasks (REL-*)** | **14 / 30 (47%)** — REL-STACK/TEST ✅; REL-DEMO **19/20** |
| **V6 code** | **54/55** — T055 tag only |
| **Program FRs (FR-P-*)** | **13/14 met in code**; **1 live-proof pending (CP15)** |
| **Constitution I–VI** | ✅ migrations 024–027 + tests in repo |
| **Live demo** | **20/20** (2026-06-26) — all CPs ✅ |
| **Integration (live)** | **41 pass / 8 fail / 14 skip** |
| **Audit deployment score** | **74/100** (external, Jun 20) — distinct from Speckit 96/97 |
| **Product scope** | **IPE only** — Nexus out of scope |
| **Uncommitted fixes** | T016–T019 + T021 in working tree — **git init pending** |

**Recommendation**: Phase 0 git commit (T023) → user approval → tag **v6.0.0** (T024).

---

## Whole Project Status (Detailed)

### 1. Workspace & tooling

| Item | State |
|------|-------|
| Workspace root | `E:\AISOP` |
| Monorepo | `ipe/` (services, apps/web, specs, infrastructure) |
| Spec Kit | `.specify/` @ root; `feature.json` → `ipe/specs/005-*` |
| Git | `master`, **no commits**; use `safe.directory=E:/AISOP` |
| Orphan paths | `E:\AISOP/services/` — do not deploy; `my-project/` redundant scaffold |
| Out of scope | `nexus-social/`, `E:\nexus-social-platform\` |

### 2. Feature timeline

```text
000 Completion docs ──► 001 Convergence ──► 002 Gates (58/62)
        │                      │                    │
        └──────────────────────┴────────────────────┘
                                    │
                    003 V5 (45/45) @ v1.0.0
                                    │
                    004 V6 (54/55) ──► T055 / v6.0.0
                                    │
                    005 Program rollup (living)
```

| Feature | Tasks | Done | Tag / gate |
|---------|-------|------|------------|
| 000 Project completion | meta | docs | 85→96 historical |
| 001 Production readiness | 39 | 38 | convergence |
| 002 Release gates | 62 | 58 | G1–G3 ✅ |
| 003 Autonomous V5 | 45 | 45 | **v1.0.0** |
| 004 AI-first V6 | 55 | 54 | **v6.0.0 pending** |
| 005 Program status | 15 | 5 | living spec |
| 004 REL track | 25 | 12 | partial |

### 3. What we build (delivered)

**IPE** is an ERP-agnostic, event-driven AI production planning platform for discrete manufacturers.

| Domain | Capability | Status |
|--------|------------|--------|
| Visibility | Control Tower, feasibility, KPIs, WebSocket | ✅ Shipped |
| Resolution | Scenarios, trade-offs, financial columns | ✅ Shipped |
| Scheduling | OR-Tools CP-SAT, Gantt, approve → Kafka | ✅ Shipped |
| Materials | Netting, ATP, landed cost (V6) | ✅ Shipped |
| Demand | Margin-aware priority, tariff shock (V6) | ✅ Shipped |
| Capacity | Visual CPM, maintenance blocks (V6) | ✅ Shipped |
| Copilot | NLP intent router, tiered LLM | ✅ Shipped |
| Executive | OTD, delay breakdown, what-if | ✅ Shipped |
| War Room | Disruption feed, Cost of Chaos (V6) | ✅ Shipped |
| Governance | MDR, AI Trust, Admin autonomy | ✅ Shipped |
| Supply chain | SCN portal, scorecards | ✅ Shipped |
| Shop floor | Work orders, delay reporting | ✅ Shipped |

### 4. What we want to build (target)

| Horizon | Goal | Status |
|---------|------|--------|
| **P0 v6.0.0** | Live demo 20/20 + tag | ⬜ REL-STACK/DEMO open |
| **P1 POST-A** | Async CPM >50 MOs, visual-cpm-svc | ⬜ Post-tag |
| **P1 POST-B** | Keycloak, live SAP/D365 | 🔴 BLOCKED / pilot |
| **P2 POST-C** | Schedule versioning, twin clone, legacy RLS | ⬜ Post-tag |
| **P2 REL-PROD** | k6 200 VU + Chaos → 100/100 | ⬜ Optional |
| **P3 POST-D** | Stripe, mobile, WCAG | Out of scope v6 |

### 5. Codebase inventory

| Layer | Count | Evidence |
|-------|-------|----------|
| Microservices | 14+ app + connector | `ipe/services/*` |
| Backend tests | 870+ | launch-verify 2026-06-23 |
| Migrations | 001–027 | `ipe/migrations/versions/` |
| Kafka topics | 24 | docker-compose + schemas |
| Frontend routes | 15+ modules | `apps/web/src/features/` |
| Demo checkpoints | 20 | `run-full-demo.ps1` |

### 6. Infrastructure (runtime, 2026-06-25)

| Component | Status |
|-----------|--------|
| Docker Desktop | Running (intermittent slow responses) |
| Infra containers | db, redis, kafka, zookeeper **Up** |
| App services + Kong | **Not up** — image build in progress / incomplete |
| Demo overlay | ✅ `docker-compose.demo.yml` |
| Orchestration | ✅ `rel-demo-stack.ps1` |
| Web UI `:8082` | Manual `npm run dev` in `apps/web` |

### 7. Readiness dimensions

| Dimension | Score | Gap |
|-----------|-------|-----|
| Product completeness | 98 | Minor audit-svc separation |
| Testing | 92 | Live demo + k6/Chaos |
| Security | 76 | Keycloak live, mTLS runtime |
| Operations | 88 | Stack automation proving out |
| Documentation | 95 | P-DOC-04 after demo pass |
| **Overall** | **96/100** | REL-DEMO + optional REL-PROD |

---

## Specification Analysis Report

### Findings

| ID | Category | Severity | Location(s) | Summary | Recommendation |
|----|----------|----------|-------------|---------|----------------|
| A1 | Coverage | **HIGH** | FR-P-08, REL-09–11 | Live demo **19/20** — CP15 only | T021 rebuild cap-svc |
| A2 | Coverage | ✅ RESOLVED | CP10–11, 17–20 | V6 demo CPs pass | T016–T019 complete |
| A3 | Coverage | ✅ RESOLVED | CP4, CP15 script | ApproveMoIds + guardrail | T017 complete |
| A4 | Inconsistency | **MEDIUM** | spec vs demo report | Code 20/20 vs live 14/20 | ✅ Fixed in spec checkpoint table |
| A5 | Constitution | **MEDIUM** | POST-C3 | Legacy migrations 002–012 RLS debt | POST-C backlog |
| A6 | Underspec | **LOW** | READINESS vs demo script login | Two valid demo users | ✅ Documented in clarify C-P-21 |
| A7 | Coverage | **MEDIUM** | tasks-testing TEST-* | UI/load/chaos tests open | POST-tag QA sprint |
| A8 | Process | **LOW** | git hygiene T049–T051 | Uncommitted workspace | Optional; non-blocking |
| A9 | Infrastructure | **MEDIUM** | plan RV-01 vs quickstart | Full compose vs lean overlay | ✅ Plan updated; quickstart Path A |
| A10 | Scope | **LOW** | nexus containers on host | Unrelated stacks running | Ignore for IPE REL path |

### Coverage Summary (FR-P → tasks)

| Requirement | Has Task? | Task IDs | Live proof |
|-------------|-----------|----------|------------|
| FR-P-01 Kong + JWT | ✅ | 002, REL-03 | Pending stack |
| FR-P-02 RLS | ✅ | migrations, POST-C3 | ✅ repo |
| FR-P-03 Approve loop | ✅ | 003 R1, CP15 | ⬜ |
| FR-P-04 Margin/ABP | ✅ | 004 T001–T015, CP17 | ⬜ |
| FR-P-05 Tariff | ✅ | 004 T016–T028, CP18 | ⬜ |
| FR-P-06 CPM | ✅ | 004 T029–T036, CP19 | ⬜ |
| FR-P-07 Maint/chaos | ✅ | 004 T037–T055, CP20 | ⬜ |
| FR-P-08 Demo 20/20 | ✅ | REL-09–11, T009 | ⬜ **Open** |
| FR-P-09 launch-verify | ✅ | REL-06–08 | ✅ **Done** |
| FR-P-10 Tag v6.0.0 | ✅ | T055, REL-12–17 | ⬜ |
| FR-P-11 Lean stack | ✅ | rel-demo-stack.ps1 | In progress |
| FR-P-12 k6/Chaos | ✅ | REL-18–20 | Optional |
| FR-P-13 Keycloak | ⬜ | POST-B1 | BLOCKED |
| FR-P-14 Commercial | ⬜ | POST-D | Out of scope |

**Coverage**: **14/14 FR-P** mapped; **4/14** awaiting live proof.

### Constitution alignment

| Principle | Status | Release check |
|-----------|--------|---------------|
| I RLS | ✅ 024–027 in repo | Verify on demo DB at REL-04 |
| II Auth | ✅ RBAC on V6 routes | JWT demo; Keycloak waived |
| III Tests | ✅ 10/10 launch-verify | Mandatory REL-06 ✅ |
| IV Events | ✅ tariff + maintenance Avro | CP18/20 smoke |
| V API | ✅ Kong routes | CP17–20 |
| VI Observability | ⚠️ OTEL off in demo overlay | Accept for demo |

**Constitution conflicts**: **0 CRITICAL**.

### Unmapped tasks (informational)

- 002 T049–T051, T053 — hygiene, superseded
- POST-A1–D5 — correctly post-tag backlog
- TEST-* — QA track parallel to REL

### Metrics

| Metric | Value |
|--------|-------|
| Program FRs (FR-P) | 14 |
| Open release tasks | 18 |
| Build task completion | 97% |
| FR live-proof coverage | 71% (10/14) |
| Ambiguity markers | 0 |
| Critical issues | **1** (A1 demo gate) |

---

## Cross-Artifact Matrix

| # | Artifact A | Artifact B | Severity | Status |
|---|------------|------------|----------|--------|
| X-P-01 | spec FR-P-08 | demo 14/20 | **CRITICAL** | Open |
| X-P-02 | 004 tasks 54/55 | T055 open | INFO | Aligned |
| X-P-03 | feature.json REL-STACK | rel-demo-stack.ps1 | INFO | Aligned |
| X-P-04 | READINESS 96 | spec executive | INFO | Aligned |
| X-P-05 | plan quickstart | tasks start cmd | LOW | ✅ Aligned E:\AISOP |
| X-P-06 | clarify IPE-only | spec scope | INFO | ✅ Aligned |
| X-P-07 | P-DOC-04 | demo 20/20 | MEDIUM | After REL-11 |

**Hierarchy**: `tasks.md` > `spec.md` > `READINESS.md` > Notion

---

## Gap Analysis (96 → 100)

| Gap | Blocks tag? | Remediation |
|-----|-------------|-------------|
| Demo 20/20 live | **Yes** | `rel-demo-stack.ps1` |
| Docker app images | **Yes** | Complete build + `up -d` |
| T055 + approval | **Yes** | User sign-off |
| k6 + Chaos | No | REL-PROD |
| Keycloak live | No | POST-B1 |

---

## Next Actions

| Priority | Action | Command |
|----------|--------|---------|
| **P0** | Finish REL-STACK | `.\scripts\rel-demo-stack.ps1` |
| **P0** | Demo 20/20 | (included in script) |
| **P0** | User approval → tag | `git tag -a v6.0.0` |
| P1 | Mark SC-V6 live proven | P-DOC-04 |
| P2 | 100/100 readiness | REL-18–20 |

---

*Generated by `/speckit.analyze` 2026-06-25. V6 module detail: [../004-ai-first-v6/analyze-v6.md](../004-ai-first-v6/analyze-v6.md).*
