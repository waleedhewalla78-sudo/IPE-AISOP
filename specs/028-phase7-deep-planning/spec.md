# Feature Specification: Phase 7 Deep Planning & Operations Intelligence

**Feature Branch**: `028-phase7-deep-planning`

**Created**: 2026-07-16

**Status**: Active — Wave 1 / MVP eng COMPLETE

**Input**: `IPE-Phase7-Deep-Planning-Operations.md`. Phase 6 went wide (17 agents, 9 modules). Phase 7 goes **deep** into the 5 core disciplines — Planning, S&OP, Demand, Production, Operations — building ON the existing dpe-svc `planning-command` (phase5) + `enterprise` (phase6) cores. Do NOT wipe Phase 3-6.

**Gate**: Started only after the Phases 3-5 E2E strategy RE-RUN closed (commit `50c908f`). Final verdict **CONDITIONAL** — 102 cases, **86 PASS / 0 FAIL / 15 SKIP / 1 BLOCKED**; all 10 baseline unit suites PASS. The re-run confirmed **no genuine product-code defects** (prior FAILs were harness bugs, a stale dpe-svc image now rebuilt, and a compose-env gap). Foundations (dpe-svc phase4/phase5) verified green → PROCEED.

**Out of scope (honest MOCK/SCAFFOLD or deferred)**:
- Live IoT / MES machine telemetry for Digital Gemba + real-time WC status — **STUB** (`iot_live=false`, PH1-02 OPEN)
- Live operator tablet UI (A16 Standard Work) — minimal Wave 1 (compute + tracking contract only)
- Live Odoo Accounting / market-data feeds — PH1-02 OPEN (unchanged from Phase 6)
- OQ-7 pricing, SOW send, Odoo 17/19 confirmation, G-R2-04 Arabic native QA → v9.1.1-r2 — **COM OPEN**
- S&OP formal stage-gate state machine (skip-to-management_review) — governance cycle modelled as config; interactive gate DEFERRED (was E2E-SOP-03 BLOCKED)
- Monetary net-saving quantification in R2 leveling engine — DEFERRED (was P5-LEV-02 SKIP)

---

## User Scenarios

### US1 — Multi-Horizon Planning (§1) (P0)
A VP opens Planning → Horizons and sees strategic (12-24 mo), tactical (1-6 mo), and operational (0-4 wk) horizons simultaneously with per-horizon coverage health. A strategic growth decision cascades DOWN to tactical/operational actions; an operational capacity constraint escalates UP to a board capex decision.

### US2 — Financial & Rolling S&OP + Shaping + Portfolio (§2) (P1)
S&OP consensus is simultaneously a volume and a P&L decision (revenue/cost stack/margin per period with margin-floor alerts). Rolling S&OP recalculates on events (large order, supplier failure, capacity change) with a monthly 4-stage governance cycle. Demand shaping proposes mix-shift / pull-forward / outsource options. Portfolio optimization ranks products by margin per constrained work-centre hour.

### US3 — Demand Decomposition, Collaboration, NPI (§3) (P1)
Demand decomposes into base/trend/seasonal/promotional/event/noise. A multi-stakeholder collaboration produces a weighted consensus with disagreement flags and bias tracking (persistent-bias weight decay). NPI forecasting composites analogy, cannibalization, and market-sizing.

### US4 — Advanced Production Scheduling + Labour + Make-or-Buy (§4) (P1)
Sequence-dependent setup optimisation, multi-resource scheduling (binding-constraint surfacing), campaign planning (setup reduction + net-benefit), labour skills matrix with single-point-of-failure flags, and dynamic make-or-buy keyed on bottleneck utilisation.

### US5 — Operations: OEE Programme, Gemba, Andon, KPI Tree, Standard Work (§5) (P1)
OEE improvement programme with actions/investment/payback; Digital Gemba real-time WC/operator/job view (IoT stub); Andon red/yellow/blue/white escalation with trigger→resolve lifecycle; KPI tree drill-down factory→dept→WC→operator; A16 Standard Work step tracking with >120% over-standard flagging.

### US6 — Integrated Planning Calendar (§6) (P2)
Unified daily/weekly/monthly/quarterly/annual planning-activity calendar mapped to owning agents, filterable by cadence.

---

## Requirements

- **FR-001** Three-horizon model + horizon health + cascade (down/up) — `GET /planning-command/horizons`, `POST /planning-command/horizons/cascade`
- **FR-002** Financial S&OP P&L-per-consensus with margin-floor alerts — `POST /planning-command/sop/financial`
- **FR-003** Rolling S&OP event-driven recalc + 4-stage monthly governance — `POST /planning-command/sop/rolling`
- **FR-004** Demand shaping (mix-shift / pull-forward / outsource) — `POST /planning-command/sop/demand-shaping`
- **FR-005** Portfolio mix optimization by margin per constraint hour — `POST /planning-command/sop/portfolio`
- **FR-006** Demand decomposition (6 components) + composite forecast + CI — `POST /planning-command/demand/decompose`
- **FR-007** Weighted collaboration consensus + disagreement + bias tracking — `POST /planning-command/demand/collaborate`
- **FR-008** NPI forecast (analogy + cannibalization + market-sizing composite) — `POST /planning-command/demand/npi`
- **FR-009** Sequence-dependent setup optimisation — `POST /planning-command/production/setup-sequence`
- **FR-010** Multi-resource scheduling with binding-constraint escalation — `POST /planning-command/production/multi-resource`
- **FR-011** Campaign planning with setup savings + net benefit — `POST /planning-command/production/campaign`
- **FR-012** Labour skills matrix + single-point-of-failure flags — `POST /planning-command/production/labour`
- **FR-013** Dynamic make-or-buy keyed on bottleneck utilisation — `POST /planning-command/production/make-or-buy`
- **FR-014** OEE improvement programme with payback — `POST /planning-command/operations/oee-programme`
- **FR-015** Digital Gemba real-time view (IoT stub, `iot_live=false`) — `GET /planning-command/operations/gemba`
- **FR-016** Andon board + trigger + resolve lifecycle — `GET/POST /planning-command/operations/andon`, `POST .../andon/{id}/resolve`
- **FR-017** KPI tree factory→dept→WC→operator drill-down — `GET /planning-command/operations/kpi-tree`
- **FR-018** Standard Work A16 step tracking + over-standard flags — `POST /planning-command/operations/standard-work`
- **FR-019** Integrated planning calendar (filterable by cadence) — `GET /planning-command/calendar`
- **FR-020** APIs under existing `/api/v1/planning-command/*` Kong route; router registered; Kong :8000 reachable
- **FR-021** Migrations 064-067 (RLS on every new tenant table); continue from head 063
- **FR-022** React dashboards wired into Planning Hub (Horizons), Command Center (Operations Deep), Intelligence Hub (S&OP/Demand/Production Deep)
- **FR-023** Full pytest per discipline + regression; live-integration features flagged MOCK/STUB honestly

---

## Success Criteria

- Phase 7 Wave 1 eng across all 5 disciplines + calendar
- New pytest suites green + no regression to Phase 3-6
- Kong :8000 smoke of new endpoints passes
- Frontend `tsc --noEmit` clean
- COM blockers remain OPEN (unchanged, not faked)
