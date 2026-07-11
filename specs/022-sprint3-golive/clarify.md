# Clarifications — Spec 022 Sprint 3 Go-Live

**Date:** 2026-07-11  
**Method:** Full-analysis clarification (no human Q&A — pipeline runs without approval gates). Underspecified areas resolved from constitution, Sprint 2 artifacts, OPEN-ITEMS, OQ status, and live repo state.

---

## Clarification Log

### C-022-01 — What is “Sprint 3” for this Speckit feature?

**Ambiguity:** Historical docs use “Sprint 3” for OR-Tools/NLP (V5 blueprint), Phase 2 demand sensing, and enterprise gap closure.

**Decision:** For Spec **022**, Sprint 3 means **Star Trans R1 go-live readiness** after Sprint 1 engineering + Sprint 2 customer enablement — deploy dry-run, validate script evidence, status honesty, GH hygiene, live smoke. It does **not** reopen Wave 3 NL/supplier work or SAP enterprise MVP.

---

### C-022-02 — Is `v9.2.0-planning` still pending?

**Ambiguity:** Spec 021 converge said tag pending live UAT; feature.json readiness still mentioned pending.

**Decision:** Tag **`v9.2.0-planning` exists at `b04434d`**. Treat as applied. Remaining live UAT/smoke is **regression evidence**, not a precondition to invent a new planning tag. Do not retag.

---

### C-022-03 — SOW “complete” vs SOW “sendable”

**Ambiguity:** Sprint 2 claims SOW v1 complete; OQ-7 says placeholders block send.

**Decision:** Document SOW **artifact complete**, **send blocked** by OQ-7. Engineering MUST NOT invent prices. PH1-01 remains OPEN until COM fills amounts and sends.

---

### C-022-04 — Odoo 17 vs 19 recommendation conflict

**Ambiguity:** `SOW-STATUS.md` recommends 17; `OQ-RESOLUTION-STATUS.md` recommends 19 with 17 aliases.

**Decision:** Engineering supports **both** via mapper aliases. Commercial confirmation (OQ-1) remains OPEN. Spec 022 docs MUST state dual support and that **Star Trans IT confirmation** is required — no silent pick. Prefer wording: “connector validated against Odoo 19 locally; Odoo 17 aliases present; confirm with customer IT.”

---

### C-022-05 — Live Odoo vs mock Odoo for Sprint 3 evidence

**Ambiguity:** PH1-02 is OPEN; stack has `mock-odoo-api` healthy.

**Decision:** Sprint 3 engineering evidence MAY use mock Odoo / SKIP live sync. Live staging sync is **COM/ops**, not faked PASS. Validate script MUST label Odoo live checks honestly.

---

### C-022-06 — Arabic engineering vs G-R2-04

**Ambiguity:** Playwright Arabic green vs native sign-off.

**Decision:** Engineering Arabic keys/tests can PASS. **G-R2-04 remains OPEN**. Tag `v9.1.1-r2` HOLD. Never push `v9.1.0-r2`.

---

### C-022-07 — Spec 021 issues #52–#55 still OPEN

**Ambiguity:** Code shipped; issues still open.

**Decision:** Spec 022 MUST triage: close with SHA evidence if fixed on master; leave open only if residual defect proven.

---

### C-022-08 — Analyze before plan (user pipeline order)

**Ambiguity:** Official Speckit analyze agent requires tasks.md first; user ordered analyze before plan.

**Decision:** Produce **analyze.md** in two layers: (A) whole-project + constitution/spec/clarify consistency at clarify time; (B) refresh after tasks with full spec/plan/tasks coverage. Both live in the same `analyze.md`.

---

## Spec Updates Applied

Decisions above are encoded in `spec.md` FR/SC language and bind `plan.md` / `tasks.md`.

---

## Remaining Human-Only Items (not clarified away)

| ID | Owner | Note |
|----|-------|------|
| OQ-7 | Waleed | Pricing — blocks SOW send |
| OQ-1 | Star Trans IT | Odoo 17 vs 19 confirm |
| PH1-02 | Ops / Customer IT | Live Odoo staging |
| G-R2-04 | Native Arabic reviewer | Sign-off for `v9.1.1-r2` |
| OQ-9 signatures | Waleed | Gate 11 waiver Section 6 |
| OQ-8 | Waleed | Customer 2 prospect list |
