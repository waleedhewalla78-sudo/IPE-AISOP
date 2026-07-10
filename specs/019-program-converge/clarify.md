# Clarifications: 019-program-converge

**Date**: 2026-07-10  
**Mode**: Non-interactive full pipeline (recommended defaults applied and encoded into spec)

## Q1 — Feature folder strategy

**Recommended:** Option A — create `019-program-converge` (do not overwrite 005/017/018 history).

| Option | Description |
|--------|-------------|
| A | New `019-program-converge` program feature |
| B | Update `005-ipe-program-status` in place |
| C | Append only to `018-phase2-release2` |

**Decision**: A — preserves sprint history; 005 remains archival rollup pointer.

## Q2 — Commercial / human blockers

**Recommended:** Option A — keep OPEN; never mark complete in Speckit implement.

| Option | Description |
|--------|-------------|
| A | Leave PH1-01, PH1-02, Arabic native sign-off OPEN |
| B | Mark "waived" for demo tag |
| C | Close with engineering proxy evidence |

**Decision**: A — constitution honesty; no fake commercial completion.

## Q3 — Wave 2 incomplete items (#37/#38/#40/#42)

**Recommended:** Option B — implement #40 promote now; defer #37/#38/#42 with issue comments.

| Option | Description |
|--------|-------------|
| A | Implement all Wave 2 open items this pass |
| B | Implement promote (#40); defer provision/quotas/ML E2E |
| C | CUT all Wave 2 remaining |

**Decision**: B — highest ROI unblocked gap is promote; SaaS metering/ML need more design.

## Q4 — stock.quant (FR-R1-05 / C-15)

**Recommended:** Option A — fix mock-odoo fidelity; treat connector path as eng-done for local E2E; staging still PH1-02.

| Option | Description |
|--------|-------------|
| A | Mock fidelity + tests; staging Odoo remains PH1-02 |
| B | Full live Odoo staging required before any close |
| C | ARB CUT stock.quant from R1 |

**Decision**: A — code path exists; empty mock was the false gap.

## Q5 — R2 tag policy

**Recommended:** Option A — HOLD `v9.1.1-r2` until G-R2-04 human sign-off policy; do not move old `v9.1.0-r2`.

| Option | Description |
|--------|-------------|
| A | HOLD tag; document eng-green + human-open |
| B | Tag now on eng gates alone |
| C | Push existing `v9.1.0-r2` as-is |

**Decision**: A — aligns with OPEN-ITEMS and constitution VIII evidence discipline.

## Coverage map (post-clarify)

| Category | Status |
|----------|--------|
| Functional scope | Clear |
| Domain/data | Clear (scenario status, stock.quant) |
| UX | Clear (promote button) |
| NFR | Clear (tests, tenant isolation, port safety) |
| Integrations | Clear (mock vs staging) |
| Edge cases | Clear |
| Completion signals | Clear |
| Commercial blockers | Explicit OPEN |
