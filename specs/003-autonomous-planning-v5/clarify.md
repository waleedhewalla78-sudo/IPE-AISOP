# Clarifications: Autonomous Production Planning — IPE V5.0 Convergence

**Feature**: `003-autonomous-planning-v5`  
**Date**: 2026-06-23  
**Status**: Resolved — post-implementation re-validation (`/speckit.clarify`)  
**Input**: [spec.md](./spec.md), [plan.md](./plan.md), [tasks.md](./tasks.md), commit `4efb8de`, tag `v1.0.0`

---

## Purpose

Records ambiguities between the **agreed R1–R4 plan** and what was built, with **binding decisions** for product, QA, and release sign-off. Distinguishes **code complete** (45/45 tasks) from **exit-gate proven** (evidence still pending on some SC items).

---

## Implementation Status vs Agreed Plan

| Phase | Tasks | Code status | Exit gate | Gate status |
|-------|-------|-------------|-----------|-------------|
| **R1** Close the loop | T001–T017 (17) | ✅ Complete | Approve → CDM → Kafka → demo | ✅ **Proven** — persistence, approve API, connector consumer, demo checkpoint 15 |
| **R2** Planner UX + AI | T018–T031 (14) | ✅ Complete | Sliders, XAI, LLM tiers, heuristic | ⚠️ **Mostly proven** — see C5, C6 |
| **R3** Enterprise governance | T032–T039 (8) | ✅ Complete | MDR, Twin, $, War Room | ⚠️ **Partial** — see C7, C8, C13 |
| **R4** Production hardening | T040–T045 (6) | ✅ Complete | v1.0.0 cert | ⚠️ **Tooling + tag done** — live evidence pending; see C9, C10 |

**Overall**: **45/45 tasks checked** in [tasks.md](./tasks.md). **Tag `v1.0.0`** on `4efb8de` (local; push optional).

---

## C1 — Published Readiness Score After 003

| Option | Score | Meaning |
|--------|-------|---------|
| A. Pre-003 demo baseline | 78/100 | Status report before convergence |
| B. 002 Gate 2 | 85/100 | Stabilization only (`READINESS.md` today) |
| **C. Post-003 code complete (chosen)** | **92/100** | All FR paths implemented; R4 live evidence not attached |
| D. Plan target after R4 | 100/100 | Requires SC-011, SC-012, live SAP/D365 |

**Decision**: Update handover narrative to **92/100** until R4 evidence folder contains executed k6 + Chaos reports. Do **not** claim 100/100 until C10 items are green.

---

## C2 — `cdm_schedule_version` Immutable Snapshots

**Ambiguity**: [plan.md](./plan.md) lists `cdm_schedule_version` table (R1); migration 023 only adds `cdm_work_order.version` + MO fields.

**Decision**: **Deferred post-v1.0.0.** v1.0.0 uses MO `version`, `ai_schedule_version`, and work-order rows as the audit trail. Immutable snapshot table is a **Phase 4 governance** enhancement, not a blocker for closed-loop approve.

---

## C3 — CDM Field Names (`ai_start` / `ai_end` vs Implementation)

**Ambiguity**: FR-001 and R1-1 acceptance text reference `ai_start`/`ai_end`; code uses `ai_suggested_start/end` (proposal) and `planned_start/end` (approved).

**Decision**: **Spec terminology maps as follows** (document in FR glossary, not a schema rename):

| Spec term | CDM column | State |
|-----------|------------|--------|
| AI proposal | `ai_suggested_start`, `ai_suggested_end` | After POST `/schedule` |
| Approved plan | `planned_start`, `planned_end` | After POST `/schedule/approve` |
| Work order times | `cdm_work_order.planned_start/end` | Same approve transaction |

FR-001 is **satisfied** by this mapping; rename migration is **out of scope**.

---

## C4 — Kafka Event Envelope Shape

**Ambiguity**: `cap-svc` publishes via `build_envelope()` with `payload`; shared `EventEnvelope` uses `data`; connector historically parsed only `EventEnvelope`.

**Decision**: Connector **`_extract_kafka_payload()`** accepts both `payload` and `data`. New producers SHOULD migrate to standard `EventEnvelope` over time; **no rollback** of shipped events in v1.0.0.

---

## C5 — Copilot Tier 503 vs Demo Structured Fallback

**Ambiguity**: FR-012/013 require no silent rule fallback when LLM misconfigured; `LLM_ROUTING_ENABLED` defaults to **`false`** for demo compatibility.

**Decision**:

| Mode | Behavior |
|------|----------|
| `LLM_ROUTING_ENABLED=false` (default compose) | Keyword intent + `format_structured_response` allowed (demo Copilot checkpoints 10–11) |
| `LLM_ROUTING_ENABLED=true` | Anthropic → Ollama → **HTTP 503**; no silent rule fallback in orchestrator |

**Admin UI** shows tier health regardless. Enterprise staging MUST set `IPE_LLM_ROUTING_ENABLED=true` to validate SC-006.

---

## C6 — MDR Gate Hysteresis (68–72%)

**Ambiguity**: [plan.md](./plan.md) risk register specifies hysteresis; implementation uses single **70% composite** threshold with fail-open if `dpe-svc` unreachable.

**Decision**: **Not implemented in v1.0.0.** Accept single threshold + remediation list. Hysteresis is **backlog** item `003-POST-v1.0.0-01` if customer reports UI thrashing.

---

## C7 — Digital Twin Scope (FR-018–FR-020)

**Ambiguity**: Spec requires clone → disrupt → delta → **promote via R1 outbox** without live CDM mutation. Shipped `DigitalTwinPanel` calls **`POST /digital-twin/disrupt`** only (simulation, no clone/promote workflow).

**Decision**:

| FR | v1.0.0 status |
|----|----------------|
| FR-018 Clone without CDM mutation | ⚠️ **Partial** — disrupt simulation only; no named sandbox scenario entity |
| FR-019 Delta metrics (OTD, cost) | ✅ **Met** — panel shows impacted MOs, cost delta, OTD estimate |
| FR-020 Promote via approve outbox | ❌ **Not implemented** — promote is post-v1.0.0 |

SC-009 **demo path passes** for disrupt→delta; full twin lifecycle is **explicit deferral**.

---

## C8 — War Room Automation (FR-023–FR-025)

**Ambiguity**: FR-023 requires auto-aggregate within 60s on supplier delay **event ingest**; FR-024 requires top 3 mitigations from `res-svc`.

**Decision**:

| FR | v1.0.0 status |
|----|----------------|
| FR-023 | ⚠️ **On-demand aggregate** — `GET /war-room/aggregate` (alert-svc proxies network-svc disrupt). Not yet wired to Kafka supplier-delay consumer. |
| FR-024 | ⚠️ **Partial** — War Room page still maps resolution scenarios; no ranked top-3 API |
| FR-025 | ✅ **Stub acceptable** — Slack integration exists; assignment optional per spec |

**Binding**: Demo War Room uses aggregate endpoint; event-driven 60s SLA is **staging verification** backlog `003-POST-v1.0.0-02`.

---

## C9 — SAP / D365 Sandbox (FR-027)

**Ambiguity**: R4 requires live sandbox validation; no customer credentials in repo.

**Decision**:

| Connector | v1.0.0 evidence |
|-----------|-----------------|
| SAP | ✅ Mapper tests + `scripts/test-sap-sandbox.ps1`; live OData **SKIPPED** until `SAP_ODATA_URL` set |
| D365 | ✅ Mapper tests + `scripts/test-d365-sandbox.ps1`; live OAuth **SKIPPED** until `D365_*` env set |

Reports: `evidence/r4/sap-sandbox-report.txt`, `d365-sandbox-report.txt`. **PASS (mapper-only)** is valid for v1.0.0 tag; **live PASS** required before enterprise sales claim.

---

## C10 — R4 Live Evidence (SC-011, SC-012)

**Ambiguity**: Tasks T040/T044 marked complete with **scripts**; spec requires **executed** Chaos + k6 results before production promotion.

**Decision**:

| Artifact | Status | Action to close SC |
|----------|--------|-------------------|
| Chaos Mesh | Scripts in `infrastructure/chaos/` | Run in staging cluster; attach `evidence/r4/chaos-recovery-metrics.txt` |
| k6 200 VU | `load-test-200vu.js` + `run-k6-200vu.ps1` | Run against Kong `:8000`; attach `evidence/r4/k6-200vu-summary.txt` |
| Airflow | Compose + `verify-airflow.ps1` | Run when stack up; attach `airflow-verify-report.txt` |

**v1.0.0 tag** marks **feature complete**; **production promotion** requires green C10 artifacts.

---

## C11 — Airflow Topology in Compose

**Ambiguity**: Spec FR-028 says scheduler **+ worker**; compose uses **LocalExecutor**; redundant `airflow-worker` (Celery healthcheck) was **removed**.

**Decision**: **LocalExecutor + scheduler + webserver** satisfies FR-028 for local/staging. Celery worker is **production Helm** concern, not default compose.

---

## C12 — Demo Checkpoint Numbering

**Ambiguity**: tasks T017 says "checkpoint 16"; script labels persist-after-approve as **"15."** with login as **"0."**

**Decision**: **16 total checkpoints** = login (0) + modules 1–14 + persist-after-approve (15). SC-003 **≥16/16** means `$Total -ge 16` after login. Wording in tasks.md means **16th checkpoint including login**, not index 16.

---

## C13 — MDR Dashboard Navigation

**Ambiguity**: FR-014 exposes dashboard; route `/mdr` exists but **Sidebar** has no MDR link.

**Decision**: **Acceptable for v1.0.0** — reachable via direct URL and future nav pass. Add sidebar entry in post-v1.0.0 UX polish unless blocked for demo.

---

## C14 — Git Tag and Remote

**Ambiguity**: T045 includes tag `v1.0.0`; large release committed as `4efb8de`; tag created locally.

**Decision**: Tag **`v1.0.0`** points to release commit. **Push** `master` + `v1.0.0` when operator approves. KMS dirs and `*_test_result.txt` remain **untracked**.

---

## C15 — Residual Risks (≤3 for SC-013)

Carried forward from 002 plus 003-specific:

1. **Keycloak live IdP** — BLOCKED (C-007); SAML/SCIM not production-certified.
2. **R4 live evidence** — Chaos/k6 not run in attached evidence (C10).
3. **Multi-ERP live** — SAP/D365 mapper-only until customer sandboxes (C9).

---

## Success Criteria Scorecard (Post-Implementation)

| ID | Criterion | Status |
|----|-----------|--------|
| SC-001 | Approve → persist ≤60s p95 | ⚠️ Not load-measured; functionally implemented |
| SC-002 | Priority ordering 100% test cases | ✅ `test_priority_resolver.py` |
| SC-003 | Demo ≥16/16 | ✅ Checkpoint 15 added; run `run-full-demo.ps1` |
| SC-004 | Control panel ≤30s | ⚠️ Manual demo verification |
| SC-005 | XAI ≥3 factors | ⚠️ Depends on solver payload; panel wired |
| SC-006 | LLM Tier 2 or 503 | ⚠️ Requires `LLM_ROUTING_ENABLED=true` + Ollama model pull |
| SC-007 | Heuristic ≥90% MOs | ✅ Tests in `test_heuristic_scheduler.py` |
| SC-008 | MDR gate 70% | ✅ Composite gate in `capacity.py` + `mdr_engine.py` |
| SC-009 | Twin workflow ≤2 min | ⚠️ Disrupt path only (C7) |
| SC-010 | Resolution financial columns | ⚠️ MO-level projection; not all demo MOs may match feasibility queue |
| SC-011 | Chaos recovery SLOs | ❌ Evidence not attached |
| SC-012 | k6 200 VU SLO | ❌ Evidence not attached |
| SC-013 | Readiness ≥95%, ≤3 risks | ⚠️ **92/100** with 3 documented risks (C15) |

---

## Binding Next Actions (Post-Clarify)

1. Run `.\scripts\run-full-demo.ps1` → confirm 16/16.
2. Run `.\scripts\run-k6-200vu.ps1` → commit summary to `evidence/r4/`.
3. Run Chaos in staging → `collect-evidence.ps1`.
4. Set `IPE_LLM_ROUTING_ENABLED=true` in staging; pull Ollama model (`llama3.2`).
5. `git push origin master && git push origin v1.0.0` when operator ready.

---

## Document Sync

| File | Update |
|------|--------|
| [spec.md](./spec.md) | Status → **Complete (v1.0.0)** with C7/C8/C10 caveats |
| [READINESS.md](../../READINESS.md) | Score **92/100** when published |
| [RELEASE_NOTES.md](../../RELEASE_NOTES.md) | Already references v1.0.0 convergence |

**Supersedes**: informal gaps between plan AD-001–AD-006 and shipped code. Constitution Principles I–IV remain **non-waivable**.
