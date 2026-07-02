# Clarify — 014 Release 2 Commercial Growth

**Date**: 2026-07-01  
**Feature**: `014-release2-growth`  
**Input**: Strategic assessment 2026-06-30, 013 converge 96/100, RELEASE1-DEMO-STATUS

---

## Open questions resolved

| ID | Question | Decision | Rationale |
|----|----------|----------|-----------|
| OQ-R2-1 | Auto-propose trigger: Kafka vs HTTP? | **HTTP from connector after rescore** for release1; keep Kafka consumer as secondary | R1 compose has no Kafka; connector already calls fea-svc HTTP |
| OQ-R2-2 | Copilot Lite: nlp-svc or dpe-svc? | **dpe-svc `/planner-assist/query`** structured router for R2; optional nlp-svc passthrough in hybrid | Avoids Ollama RAM on 8 GB VM; reuses existing API fetchers pattern |
| OQ-R2-3 | Feasibility threshold for auto-propose? | **75% default**, tenant config key `auto_propose_threshold` | Aligns with "at risk" band; 85% is approve gate not propose gate |
| OQ-R2-4 | Duplicate scenarios on re-sync? | **Upsert by (mo_id, strategy)** — skip if identical strategy exists with status proposed | Idempotent sync |
| OQ-R2-5 | Odoo write-back scope in R2? | **Chatter notes P1**; draft PO **P2** if UAT time constrained | Lower risk first |
| OQ-R2-6 | R2 before or after 013 tag? | **Engineering parallel OK**; customer-facing R2 after T071 UAT + v9.0.0-r1 tag | Constitution VII customer-first |
| OQ-R2-7 | Outcomes vs Executive tab? | **New Outcomes tab** in release1; full Executive remains hybrid | R1 nav trim — Outcomes is CEO-focused subset |
| OQ-R2-8 | Arabic for R2 strings? | **Required** for Outcomes + Copilot Lite labels (same as R1 MVP) | Star Trans MENA |

---

## Underspecified areas — defaults applied

| Area | Default |
|------|---------|
| Copilot Lite LLM | Structured templates only in release1 compose |
| Scenario count per MO | 3–5 (match `generate_strategies` output) |
| QBR export format | Browser print + clipboard JSON summary |
| Second customer ERP | Odoo assumed; SAP remains 015+ |

---

## Clarification markers

No `[NEEDS CLARIFICATION]` items remain — all resolved above.

---

## Dependencies

| Dependency | Owner | Status |
|------------|-------|--------|
| 013 T071 UAT | Customer + Eng | Blocked T003 |
| 013 v9.0.0-r1 tag | Eng | Blocked T071 |
| res-svc in release1 compose | Eng | ✅ Done 2026-06-30 |
| MDR seed for scheduling | Eng | ✅ Done |

---

## Risk register (clarified)

| Risk | Mitigation |
|------|------------|
| Odoo custom fields break write-back | Feature flag `odoo_resolution_writeback_enabled` default false until UAT |
| Copilot hallucination | Structured path only; no LLM on release1 |
| Scenario spam on frequent sync | Threshold + dedupe by strategy |
