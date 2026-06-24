# Clarify: IPE V6.0 — Binding Decisions (Full Analysis)

**Feature**: `004-ai-first-v6` | **Updated**: 2026-06-21  
**Baseline**: `003-autonomous-planning-v5` @ v1.0.0 (`4efb8de`)  
**Inputs**: [spec.md](./spec.md), [plan.md](./plan.md), [analyze-v6.md](./analyze-v6.md), [converge-v6.md](./converge-v6.md), [../003-autonomous-planning-v5/clarify.md](../003-autonomous-planning-v5/clarify.md)

---

## Purpose

Resolves ambiguities found in `/speckit.analyze`, `/speckit.converge`, and implementation review. Distinguishes **code complete** (54/55 tasks) from **exit-gate proven** (live demo + tag pending). All decisions below are **binding** for v6.0.0 sign-off unless amended via constitution SemVer PR.

---

## Status Model (underspecified in analyze vs tasks)

| Term | Definition | V6 state |
|------|------------|----------|
| **Code complete** | All implementation tasks merged in monorepo | **54/55** — T001–T054 ✅ |
| **Exit-gate proven** | SC-V6-01–08 demonstrated on live stack | ⬜ pending RV-02, RV-03 |
| **Release artifact** | Annotated git tag | **T055** ⬜ — requires stakeholder approval |

**Decision (C-V6-08)**: `analyze-v6.md` line "55/55 implemented" means **implementation code exists**; **T055 tag is not done** until RV-02 + RV-03 pass. Task counts use **tasks.md** as source of truth.

---

## C-V6-01 — Qwen source chats (Phase 3 spec input)

**Decision**: Qwen Studio shared chats were not machine-readable (mobile shell only). V6-R3–R5 scope follows in-repo contracts (`contracts/v6-r3-visual-cpm.md` through `v6-r5-chaos-warroom.md`) and `plan.md` AD-007–AD-013.

**Impact**: No divergence from speckit plan; validation uses contracts + demo checkpoints 18–20.

---

## C-V6-02 — Auth for demo vs production

**Decision**: Demo and staging use **JWT auth** (`admin@demo.com` / `demo` @ `:8082`). Keycloak OIDC / SAML / SCIM remain **BLOCKED** (inherits 002 C-007) — not required for v6.0.0 @ 96/100.

**Impact**: Cost of Chaos RBAC uses **`executive`** role as CFO-equivalent read scope. No live IdP integration in this release.

---

## C-V6-03 — ERP connectors

**Decision**: **Mock Odoo only** for write-back. SAP/D365 mappers exist (003 R4) but live sandboxes are out of scope.

**Impact**: Tariff substitute drafts and MDR routing corrections enqueue connector actions with **`pending_approval`** — no autonomous ERP write without human approve.

---

## C-V6-04 — Production hardening evidence

**Decision**: k6 200 VU and Chaos Mesh **scripts exist** (`tests/performance/k6/`, `infrastructure/chaos/`, `scripts/r4-verify.ps1`) but live evidence is **not attached**. Readiness capped at **96/100** until evidence run; **100/100** requires executed k6 + Chaos reports in evidence folder.

**Impact**: READINESS.md residual risks; LAUNCH-CHECKLIST optional R4 step. Not a blocker for v6.0.0 tag at 96/100.

---

## C-V6-05 — Visual CPM service split

**Decision**: CPM implemented as **`cap-svc` module** (`visual_cpm.py`, `POST /capacity/cpm/cascade`) per AD-007. Split to `visual-cpm-svc` deferred post-v6.0.0.

**Impact**: Single deployable; reuses 003 schedule persistence and approve flow.

---

## C-V6-06 — Guardrail harmonization (85% vs 90%)

**Ambiguity**: FR-I-06 says block at **85%** feasibility; 003 fea-svc auto-confirm at **90%**.

**Decision**:

| Threshold | Service / path | Action |
|-----------|----------------|--------|
| **<85%** | `cap-svc` approve + `connector` ERP write | **Block**; emit `autonomy_downgraded_to_suggest` |
| **≥85% and <90%** | fea-svc | Queue for planner (Suggest path) |
| **≥90%** + autonomous mode | fea-svc | `auto_confirmed` (unchanged from 003) |

Not a conflict — different gates for **ERP write safety** vs **autonomy tier**.

---

## C-V6-07 — Phase ordering

**Decision**: Implementation order R1 → R2 → R3 → R4 → R5. R3 may overlap R2 tail; all five phases required for v6.0.0 readiness narrative @ 96/100.

---

## C-V6-08 — Code complete vs tag (see Status Model)

*(Defined in Purpose section above.)*

---

## C-V6-09 — Release verification gates (T055 prerequisites)

**Ambiguity**: Spec says tag after SC-V6-05–08; docker stack was not verified live.

**Decision**: **All three required** before T055 tag:

| Gate | Command / fix | Pass criteria |
|------|---------------|---------------|
| **RV-01** | Fix duplicate `ollama` in `docker-compose.yml`; `docker compose up -d` | API @ `http://localhost:8000` |
| **RV-02** | `scripts/launch-verify.ps1` | **10/10** service test suites |
| **RV-03** | `scripts/run-full-demo.ps1` (after seed) | **20/20** checkpoints |

RV-04 (git tag) requires **explicit stakeholder approval** — agents MUST NOT tag without user request.

---

## C-V6-10 — SC-V6-03 CPM scope and SLO

**Ambiguity**: Plan SLO p95 <2s; analyze warns "large plants need async."

**Decision**:

| Context | Binding scope |
|---------|---------------|
| **v6.0.0 sign-off** | Demo tenant **≤20 MOs**; Playwright perf test + unit tests satisfy SC-V6-03 |
| **Production claim** | Plants >50 MOs require **async cascade** (post-v6.0.0); do not claim global <2s until shipped |

Prometheus CPM latency metric in cap-svc is **required** for observability; not a substitute for demo perf test.

---

## C-V6-11 — Tariff shock SLO and data source

**Ambiguity**: Plan lists **<5s** recompute; not in SC-V6-02 table.

**Decision**:

| Item | Binding |
|------|---------|
| **SC-V6-02** | 100% of **seeded** affected MOs flagged; ≥1 substitute draft on demo data |
| **Performance** | <5s is **engineering target** on demo portfolio; not a release blocker if functional tests pass |
| **Tariff matrix** | Admin UI + Excel/CSV import (T026); **no live geopolitical API** for MVP |
| **TLC accuracy** | Seeded `cdm_landed_cost_profiles`; customer matrix import path is production follow-on |

---

## C-V6-12 — Activity cost and margin inputs

**Ambiguity**: Spec assumes ERP GL or seeded matrix; missing cost behavior in US V6-1.

**Decision**:

| Case | Behavior |
|------|----------|
| Activity drivers present | `compute_margin_adjusted_priority()` uses `cdm_activity_cost_drivers` + financial projection |
| Missing COGM/cost for SKU | **Warning** status; fallback to existing `priority_score` — **not silent default** |
| v6.0.0 data | Demo seeded via `scripts/seed-demo-client.sql`; no live GL connector |

SC-V6-01 (≥8% activity-cost delta) validated on **seeded demo tenant** via checkpoint 17.

---

## C-V6-13 — Predictive maintenance (SC-V6-04)

**Ambiguity**: analyze-v6 notes checkpoint 20 "(partial)"; AD-013 lists quality-svc **or** cap-svc/iot.

**Decision**:

| Item | Binding |
|------|---------|
| **Telemetry ingress** | **`cap-svc` `/iot/telemetry`** (RUL field) for v6.0.0 demo |
| **Event** | Avro `ipe.maintenance.block_required` → cap-svc consumer injects block + partial re-solve |
| **SC-V6-04 pass** | Unit/integration: event → block → reschedule path green; **≤60s** is demo script target on live stack, not CI timeout |
| **"Partial" label** | Means checkpoint **20 combines R4+R5** in one demo step — **not** incomplete R4 code |

MDR routing draft (V6-7) is **pilot**: connector stub `sync_routing_correction`; Odoo handler logs only — satisfies FR, not production ERP sync.

---

## C-V6-14 — Cost of Chaos aggregation (AD-012)

**Ambiguity**: Daily snapshot vs real-time tail.

**Decision**:

| Layer | Implementation |
|-------|----------------|
| **Required for SC-V6-05** | `chaos_cost.py` rollup from audit + delay categories + maintenance/override signals; **≥3 non-zero $ categories** on demo |
| **Migration 027** | `cdm_chaos_cost_snapshots` for materialized daily rollups |
| **Optional tail** | `ipe.chaos.metric` Kafka topic — **not required** for v6.0.0; real-time refresh is post-release enhancement |

CFO access: **`executive`** role on `GET /analytics/cost-of-chaos` and `/cost-of-chaos` route.

---

## C-V6-15 — Generative War Room (FR-V-04)

**Ambiguity**: US V6-9 "within 60s"; 003 aggregate vs "generative" ranking.

**Decision**:

| Item | Binding |
|------|---------|
| **API** | `GET /war-room/recovery-plan` returns **top 3** scenarios ranked by `business_score_usd` with delivery + activity cost columns |
| **60s** | **Product aspiration** for disruption UX; release gate is API + UI + demo checkpoint 20 — not a CI perf test |
| **Copilot** | `get_war_room_recovery` tool (4 tools total in nlp-svc); when `LLM_ROUTING_ENABLED=true`, responses cite scenario IDs; when false, structured JSON fallback per **003 C5** pattern |
| **Extends** | 003 War Room aggregate — does not replace Resolution Center scenarios |

---

## C-V6-16 — FR-V-03 bi-directional Excel / export

**Ambiguity**: Spec mentions tariff matrix + activity drivers + MS Project; paths scattered.

**Decision**:

| Capability | Binding deliverable |
|------------|---------------------|
| Tariff / activity import | CSV/Excel path via cap-svc project-plan parser extension (T026) |
| MS Project export | Schedule page download / export endpoint (T053) — XML format |
| Gantt export | Same schedule export flow; not a separate product |

Full bi-directional **Gantt ↔ MS Project round-trip** is **out of scope** for v6.0.0 (export only).

---

## C-V6-17 — RBAC matrix (V6 routes)

**Ambiguity**: Constitution II requires RBAC; role names not centralized in spec.

**Decision**:

| Route / action | Minimum role |
|----------------|--------------|
| CPM drag + cascade confirm | `planner` |
| Tariff shock + substitute draft | `planner` |
| Cost of Chaos read | `executive` or `admin` |
| Tariff matrix import | `admin` |
| Approve schedule / ERP write | `planner` + guardrail 85% |

---

## C-V6-18 — Inherited 003 deferrals (still binding)

**Decision**: Unless a V6 FR explicitly extends, these **remain deferred**:

| Item | Source | V6 impact |
|------|--------|-----------|
| `cdm_schedule_version` table | 003 C2 | Use MO `version` + approve audit |
| Digital Twin promote/clone | 003 C7 | Panel remains simulate-only |
| Live SAP/D365 | 003 C9 | Mapper scripts only |
| Copilot silent fallback | 003 C5 | Same rules apply to war-room tool |
| Kafka envelope `payload` vs `data` | 003 C4 | Connector accepts both |

---

## C-V6-19 — Source of truth hierarchy

**Ambiguity**: Notion tracker vs repo drift.

**Decision**:

1. Task completion → `specs/004-ai-first-v6/tasks.md`
2. Product requirements → `specs/004-ai-first-v6/spec.md`
3. Binding clarifications → **this file**
4. Readiness score → `READINESS.md`
5. Notion IPE Task Tracker v2 → **mirror only**; repo wins on conflict

---

## C-V6-20 — Readiness score @ v6.0.0

**Ambiguity**: Multiple scores in docs (92, 93, 96, 100).

**Decision**:

| Score | Meaning | When to claim |
|-------|---------|---------------|
| **96/100** | V6 code complete + docs + unit/integration tests; k6/Chaos **not executed** | **Now** — pre-tag |
| **100/100** | Above + attached k6 200 VU + Chaos evidence + Keycloak only if unblocked | Post RV-05 |

Do **not** claim 100/100 at v6.0.0 tag without RV-05 evidence.

---

## Open (post-v6.0.0)

| Topic | Status | Owner trigger |
|-------|--------|---------------|
| Async CPM for >50 MOs | Deferred | Customer plant scale |
| Live Keycloak SAML/SCIM | Blocked | Customer IdP sandbox |
| Stripe billing FR-603 | Out of scope | Commercial track |
| `cdm_schedule_version` table | Deferred | Phase 4 governance |
| `visual-cpm-svc` split | Deferred | Ops team scale-out |
| Real-time Chaos tail (`ipe.chaos.metric` consumer UI) | Optional | CFO dashboard v2 |
| WCAG 2.1 AA FR-506 | Out of scope | Accessibility sprint |

---

## Clarification Index

| ID | Topic |
|----|-------|
| C-V6-01 | Qwen / contract source |
| C-V6-02 | JWT demo auth |
| C-V6-03 | Mock Odoo ERP |
| C-V6-04 | k6/Chaos evidence |
| C-V6-05 | CPM in cap-svc |
| C-V6-06 | 85% block / 90% auto |
| C-V6-07 | Phase ordering |
| C-V6-08 | Code vs tag |
| C-V6-09 | RV-01–03 gates |
| C-V6-10 | CPM SLO scope |
| C-V6-11 | Tariff shock |
| C-V6-12 | Activity cost fallback |
| C-V6-13 | Maintenance / SC-V6-04 |
| C-V6-14 | Cost of Chaos aggregation |
| C-V6-15 | War Room generative |
| C-V6-16 | Excel / MS Project export |
| C-V6-17 | RBAC matrix |
| C-V6-18 | Inherited 003 deferrals |
| C-V6-19 | Source of truth |
| C-V6-20 | Readiness scores |

**Next command**: `/speckit.implement` RV-01–RV-03 or `/speckit.plan` for post-v6.0.0 backlog.
