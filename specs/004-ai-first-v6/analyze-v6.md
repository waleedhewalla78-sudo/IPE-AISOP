# Analyze: IPE V6.0 — Cross-Artifact Consistency & Coverage

**Feature**: `004-ai-first-v6` | **Date**: 2026-06-21  
**Scope**: Program-wide (002 → 005) with V6 focus  
**Readiness**: **96/100** (code complete; live exit gates pending)

---

## Executive Summary

| Dimension | Status |
|-----------|--------|
| **Program tasks** | **157 / 162 (97%)** — 002: 58/62 · 003: 45/45 · 004: 54/55 |
| **V6 code complete** | **54/55** — T055 git tag only |
| **Exit-gate proven** | ⬜ RV-03 demo live (14/20 last run; fixes applied) |
| **launch-verify** | ✅ **10/10** (2026-06-23) — evidence `evidence/rv-02-launch-verify.txt` |
| **Constitution I–VI** | ✅ V6 migrations 024–027 + tests + Avro pairs |
| **Cross-artifact drift** | **7 stale docs** (see § Inconsistencies) |

**Recommendation**: Resolve doc drift (1h), run RV-01–RV-03, then tag v6.0.0 at 96/100.

---

## Program Status (Whole Project)

### Timeline

```text
002 Release Gates (58/62) ──► 003 V5 (45/45) @ v1.0.0 ──► 004 V6 (54/55) ──► T055 tag
         94%                         100%                      98%              ⬜
```

### Feature 002 — Release Stabilization

| Metric | Value |
|--------|-------|
| Tasks | **58/62 (94%)** |
| Gates | 1–3 ✅ signed |
| Open | T049–T051 (commit hygiene), T053 (v1.0.0-rc1 — superseded by 003 tag) |
| Contribution | CI, JWT, docker, demo framework, READINESS baseline |

### Feature 003 — Autonomous Planning V5

| Metric | Value |
|--------|-------|
| Tasks | **45/45 (100%)** ✅ |
| Tag | `v1.0.0` @ `4efb8de` |
| Readiness (standalone) | 92/100 — R4 live k6/Chaos evidence pending |
| Residual | Twin promote, live SAP/D365, `cdm_schedule_version` deferred |

### Feature 004 — IPE V6 AI-First

| Phase | Tasks | Code | Contract | Tests | Demo CP |
|-------|-------|------|----------|-------|---------|
| V6-R1 ABP | 15/15 | ✅ | v6-r1-abp | margin, activity, guardrail | 17 |
| V6-R2 Tariff | 13/13 | ✅ | v6-r2-tariff | landed_cost, tariff_shock | 18 |
| V6-R3 CPM | 8/8 | ✅ | v6-r3-visual-cpm | visual_cpm, api_cpm, perf | 19 |
| V6-R4 Maint | 9/9 | ✅ | v6-r4-predictive-maint | maintenance_block | 20 |
| V6-R5 Chaos | 9/10 | ✅ | v6-r5-chaos-warroom | chaos + war_room APIs | 20 |
| **Open** | T055 | ⬜ tag | — | — | — |

### Feature 005 — Program Status Spec

Living rollup spec; **partially stale** (see inconsistencies). Source of truth for tasks remains `*/tasks.md`.

---

## Cross-Artifact Consistency Matrix

| # | Artifact A | Says | Artifact B | Says | Severity | Resolution |
|---|------------|------|------------|------|----------|------------|
| **X-01** | `analyze-v6.md` (prior) | 55/55 implemented | `tasks.md` | T055 open | **HIGH** | Use **54/55**; tag ≠ implementation (clarify C-V6-08) |
| **X-02** | `005/spec.md` L139 | 15/55, V6-R2 next | `tasks.md`, `READINESS.md` | 54/55 complete | **HIGH** | Update 005 executive + mermaid `15/55` → `54/55` |
| **X-03** | `implementation-tracker.md` | V6-R2–R5 "⬜ To Do" | `tasks.md` | all [x] | **MEDIUM** | Refresh tracker phase tables |
| **X-04** | `implementation-tracker.md` | SC-V6-01–08 all ⬜ | `checklists/implementation.md` | phases ✅ | **MEDIUM** | Mark SC proven after live demo |
| **X-05** | `003/tasks.md` T017 | Demo **checkpoint 16** | `run-full-demo.ps1` | Labeled **"15."** persist | **LOW** | Renumber or document offset (0-based vs 003) |
| **X-06** | `005/spec.md` Notion | "bulk sync pending" | Notion (2026-06-21) | T016–T054 synced | **LOW** | Update 005 Notion table to ✅ |
| **X-07** | `SPECKIT-CHECKLIST.md` summary | "29 inconsistencies" | Header | "RESOLVED 2026-06-22" | **LOW** | Add V6 drift note; refresh dashboard counts |
| **X-08** | `005/readiness` table | "Current v1.0.0 = 92" | `READINESS.md` | **96/100** current | **MEDIUM** | Label 92 as historical; 96 as current |
| **X-09** | `plan.md` | ~52 tasks T001–T052 | `tasks.md` | 55 tasks T001–T055 | **LOW** | plan.md task count outdated |
| **X-10** | Prior session | docker duplicate `ollama` | `docker-compose.yml` | Single `ollama:` key @ L226 | **INFO** | RV-01 may be resolved; verify `compose up` |

**Authoritative hierarchy** (clarify C-V6-19): `tasks.md` > `spec.md` > `READINESS.md` > Notion mirror.

---

## Requirement Coverage (004)

### Functional Requirements → Implementation

| FR | Requirement | Phase | Code path | Tests | SC |
|----|-------------|-------|-----------|-------|-----|
| FR-I-01 | Net-margin priority | R1 | `dpe-svc/.../margin_priority.py` | test_margin_priority | SC-V6-01 |
| FR-I-03 | Activity-cost objective | R1 | `cap-svc/.../activity_objective.py` | test_activity_objective | SC-V6-01 |
| FR-I-06 | 85% guardrail | R1 | schedule_persistence + connector | test_guardrail_85 | — |
| FR-I-02 | Landed cost pATP | R2 | `mat-svc/.../landed_cost.py` | test_landed_cost | SC-V6-02 |
| FR-I-04 | Tariff shock | R2 | `dpe-svc/.../tariff_shock.py` | test_tariff_shock | SC-V6-02 |
| FR-I-05 | Maintenance blocks | R4 | iot + maintenance_blocks | test_maintenance_block | SC-V6-04 |
| FR-V-01 | Visual CPM | R3 | `visual_cpm.py`, cascade API | test_visual_cpm, perf | SC-V6-03 |
| FR-V-02 | Cost of Chaos | R5 | `chaos_cost.py`, analytics API | via demo CP20 | SC-V6-05 |
| FR-V-03 | Excel/MS Project | R2/R5 | T026 import, T053 export | partial | — |
| FR-V-04 | War Room recovery | R5 | alert-svc war_room + nlp tool | copilot_tools | SC-V6-06 |
| FR-X-01 | Tests | all | pytest + Vitest | launch-verify | — |
| FR-X-02 | RBAC | all | require_role on new routes | API tests | — |
| FR-X-03 | Avro events | R2/R4 | tariff + maintenance schemas | consumer tests | — |

**Coverage**: **12/12 V6 FRs** have mapped code. **FR-V-03** export path ✅; full Gantt↔MS Project round-trip out of scope (clarify C-V6-16).

### User Stories → Exit Gates

| Story | Gate | Code | Live demo |
|-------|------|------|-----------|
| V6-1, V6-2, V6-10 | SC-V6-01 + guardrail | ✅ | ⬜ CP17 |
| V6-3, V6-4 | SC-V6-02 | ✅ | ⬜ CP18 |
| V6-5 | SC-V6-03 | ✅ | ⬜ CP19 |
| V6-6, V6-7 | SC-V6-04 | ✅ | ⬜ CP20 |
| V6-8, V6-9 | SC-V6-05–06 | ✅ | ⬜ CP20 |

---

## Success Criteria Matrix

| ID | Target | Unit/CI | Live demo | Tag blocker |
|----|--------|---------|-----------|-------------|
| SC-V6-01 | ≥8% activity-cost delta | ✅ tests | ⬜ CP17 | No |
| SC-V6-02 | 100% seeded MOs flagged | ✅ tests | ⬜ CP18 | No |
| SC-V6-03 | p95 cascade <2s (≤20 MOs) | ✅ perf test | ⬜ CP19 | No |
| SC-V6-04 | Telemetry → block ≤60s | ✅ integration | ⬜ CP20 | No |
| SC-V6-05 | ≥3 chaos $ categories | ✅ API | ⬜ CP20 | No |
| SC-V6-06 | Top 3 recovery w/ $ | ✅ API | ⬜ CP20 | No |
| SC-V6-07 | Readiness ≥96/100 | ✅ READINESS | — | No |
| SC-V6-08 | Demo 20/20 | ✅ scripted | ⬜ RV-03 | **Yes** (per C-V6-09) |
| T055 | git tag v6.0.0 | — | — | **Yes** |

---

## Constitution Compliance (V6)

| Principle | V6 evidence | Gap |
|-----------|-------------|-----|
| **I RLS** | Migrations 024–027 | Legacy 002–012 tables — pre-existing audit debt |
| **II Auth** | JWT + RBAC on new routes | Keycloak live BLOCKED (accepted waiver) |
| **III Tests** | Phase tests + launch-verify | nlp-svc was 9/10 in prior run — re-verify |
| **IV Events** | Avro + connector handlers | `ipe.chaos.metric` optional tail not required |
| **V Architecture** | Layered cap/dpe/mat; frontend routes | — |
| **VI Observability** | CPM Prometheus histogram; /metrics on services | K8s probes may still use /health in Helm |

---

## Test & Verification Coverage

| Layer | Scope | Status |
|-------|-------|--------|
| **launch-verify.ps1** | 10 backend services | ✅ **10/10** (2026-06-23) |
| **run-full-demo.ps1** | 20 checkpoints (0–15, 17–20) | ⚠️ 14/20 — schedule scope fix + stack rebuild pending |
| **V6 unit tests** | mat, dpe, cap (landed, tariff, cpm, maint) | ✅ |
| **Playwright perf** | CPM cascade timing | ✅ in CI path |
| **k6 200 VU** | load-test-200vu.js | ⬜ script only |
| **Chaos Mesh** | infrastructure/chaos/ | ⬜ evidence not attached |
| **Coverage threshold** | 40% fail_under | ⚠️ audit R-01 residual |

---

## Gap Analysis (96 → 100)

| Gap | Severity | Blocks tag? | Mitigation |
|-----|----------|-------------|------------|
| Live demo not run | **HIGH** | Yes (C-V6-09) | RV-03 |
| launch-verify not green | **HIGH** | Yes (C-V6-09) | RV-02 |
| T055 tag pending | **HIGH** | Yes | RV-04 + approval |
| k6/Chaos not executed | Medium | No (96/100) | RV-05 for 100/100 |
| Keycloak live | Low (demo) | No | C-007 BLOCKED |
| Doc drift (7 items) | Low | No | Sync 005 + tracker |
| Demo CP numbering 15 vs 16 | Low | No | Document in quickstart |

---

## Risk Register (Active)

1. **CPM at scale** — >20 MOs may exceed 2s; async cascade post-v6.0.0 (clarify C-V6-10).
2. **Tariff TLC** — seeded profiles only; production needs customer matrix import.
3. **Chaos dashboard** — daily snapshot; real-time optional.
4. **MDR routing draft** — connector stub; not production ERP sync.
5. **Security score 76/100** — JWT demo; enterprise needs IdP.

---

## Recommended Actions

| Priority | Action | Effort |
|----------|--------|--------|
| **P0** | Run `docker compose up -d`; `launch-verify.ps1` 10/10 | 1h |
| **P0** | Run `seed-demo-client.ps1` + `run-full-demo.ps1` 20/20 | 1h |
| **P0** | Tag v6.0.0 (T055) after approval | 5m |
| **P1** | Fix 005/spec.md stale 15/55 + mermaid | 30m |
| **P1** | Refresh implementation-tracker.md phase status | 30m |
| **P2** | Execute k6 + Chaos; attach evidence → 100/100 | 1 day |
| **P2** | Align demo checkpoint numbering with 003 docs | 15m |

---

*Generated by `/speckit.analyze` — supersedes prior analyze-v6.md sections where conflicting; aligns with clarify-v6.md C-V6-08–C-V6-20.*
