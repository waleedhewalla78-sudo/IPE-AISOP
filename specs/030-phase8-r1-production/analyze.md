# Analyze — Spec 030 + Whole-Project Status (022–030)

**Date**: 2026-07-18 · **Constitution**: 1.4.2 · **HEAD baseline at analyze start**: `d83169a` (Phase 8 code uncommitted in working tree; no PHASE8 report yet at poll)  
**Source**: Phase 8 v2 doc, OPEN-TOPICS-REGISTER, PRODUCT-STATUS, Specs 022–029, Phase 3–7 reports

## Executive verdict

| Track | Verdict |
|-------|---------|
| Specs **022–028** Wave 1 | **ENG COMPLETE** |
| Spec **029** productionization | **ENG COMPLETE Wave 1**; T301 validate **BLOCKED** (stack); COM OPEN |
| Spec **030** Phase 8 Wave 1 (8A) | **IN PROGRESS** — core code present; Speckit docs/Kong/reports/status gaps closing this run |
| Commercial gate | **COM OPEN** — OQ-7, PH1-02, G-R2-04, OQ-1 — **never fake** |
| Tag `v9.1.1-r2` | **HOLD**; never push `v9.1.0-r2` |

Program is **engineering-ready for R1 demo depth** with honest degrade/mock boundaries. Go-live commercial package remains human-gated.

---

## Spec-by-spec status (022–030)

| Spec | Title | Wave 1 | Residuals | Notes |
|------|-------|--------|-----------|-------|
| **022** | Sprint 3 go-live | ENG COMPLETE | #70/#72 seed/validate | Deploy dry-run + honesty |
| **023** | Sprint 4 Wave 1 | ENG COMPLETE | GH Odoo-config issues hygiene | Admin Odoo Config v2 + OTD |
| **024** | Ops Phase 3 | ENG COMPLETE | #110 validate when Docker up | Agents + upload + predictive |
| **025** | Ops Phase 4 Premium | ENG COMPLETE | Collaborative UI deferred | M1–M6, A8–A12 |
| **026** | Ops Phase 5 Planning | ENG COMPLETE | WhatsApp hub deferred | Cockpit/MPS/MRP/ATP |
| **027** | Ops Phase 6 Enterprise | ENG COMPLETE | Live Odoo/market/IoT MOCK | A13–A17, M7–M9 |
| **028** | Ops Phase 7 Deep | ENG COMPLETE | Andon notify / tablet UI W2 | Deep disciplines 064–067 |
| **029** | Productionization | ENG COMPLETE Wave 1 | T301 #70/#72/#110; k6 under-load | Kong enterprise, Andon dual-write, RLS 068, MPS/MRP 069, stage-gate, QA notes |
| **030** | Phase 8 R1 Production | **Active 8A** | 8B–8D; COM; live write-back | Ollama/roles/Excel/write-back safety |

---

## Constitution compliance (I–X + Phase 8 honesty)

| Principle | Spec 030 check |
|-----------|----------------|
| I RLS | Migration 070 enables RLS on `cdm_write_back_log` |
| II Auth | Phase 8 routes behind JWT (same dpe-svc pattern) |
| III Tests | Dedicated unit suites for ollama/roles/phase8/upload |
| IV Events | No Kafka requirement for Wave 1 Phase 8 APIs |
| V Architecture | `phase8_production` under dpe-svc `/api/v1/phase8` |
| VI Observability | AI status endpoint + degrade banner |
| VII Customer-first / honesty | Mock write-back; G-R2-04 OPEN; no fake fine-tunes |
| VIII Gates | No enterprise tag claimed this run |
| IX Ops map | Phase 8 ≠ platform K8s phase; map updated in constitution 1.4.2 |
| X Autonomy | Role thresholds reinforce L3 approval for high impact |

---

## Concurrent Phase 8 agent absorption

Peer agent (Phase 8 R1 from Production-Ready v2) already landed (working tree):

- `ipe_shared/llm/ollama_client.py`, `roles.py`, `models/write_back_log.py`
- `dpe-svc` phase8 API + core (agents/narratives/write_back)
- upload-svc schemas + tests
- `AiDegradedBanner` + locale keys
- migration 070, ops/ollama Modelfiles
- feature flags `ipe.odoo.live_writeback`, `ipe.ollama.enabled`

**Gaps at analyze time:** Speckit depth (specify/clarify/analyze/plan/tasks/issues), Kong `/api/v1/phase8` route, PHASE8 + R1 readiness reports, PRODUCT-STATUS/feature.json/AGENTS pointers still on 029, constitution still 1.4.1, no commits after `d83169a`.

---

## Open topics (must stay OPEN)

### COM / Human (P0)

- **OQ-7** pricing → blocks SOW send (GH#106)
- **PH1-02** live Odoo staging (GH#108)
- **G-R2-04** Arabic native QA → blocks `v9.1.1-r2` (GH#109)
- **OQ-1** Odoo 17 vs 19 (GH#107)

### Engineering residuals (stack / Wave 2)

- #70 / #72 / #110 validate when R2 healthy
- QA-01 k6 p95 under load (notes only in Spec 029)
- Playwright flake notes (Spec 029)
- Phase 6/7 deferrals: live IoT, WhatsApp, tablet UI, monetary leveling

---

## Risk register (analyze)

| Risk | Severity | Mitigation |
|------|----------|------------|
| Claiming Phase 8 “production-ready” full v2 | High | Scope docs to **8A Wave 1** only |
| Live write-back accidental enable | High | Flag default false + PH1-02 message |
| Spec 029 reopen thrash | Med | Spec 030 separate; reference 029 |
| Race with Phase 8 agent commits | Med | Absorb deltas; implement gaps only |
| Stack-down validate | Med | Honest BLOCKED; do not fake PASS |

---

## Recommendation

Proceed **plan → tasks → issues → implement remaining gaps → converge** for Spec 030 Wave 1. Do not recreate 029. Do not close COM. After tests green, update status docs and cut Speckit converge as **ENG COMPLETE Wave 1 (8A)** with 8B–8D deferred.
