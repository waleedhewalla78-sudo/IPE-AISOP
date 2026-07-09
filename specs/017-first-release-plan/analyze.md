# Cross-Artifact Analysis — IPE Program (017 Rollup)

**Date**: 2026-07-09  
**Constitution**: v1.2.3  
**Sources**: Spec 015, 016, 017 · PRD · GATE-RESULTS · First Release Plan docx

---

## 1. Executive summary

| Dimension | Assessment |
|-----------|------------|
| Constitution | ✅ Compliant; Gate 11 partial documented |
| Spec 017 ↔ Downloads plan | ✅ 1:1 phase/wave mapping |
| Phase 0 completion | **~85%** — emitters done; tag blocked |
| Wave 1 | **~15%** — Copilot nav done |
| Wave 2–3 | 0% (correctly gated post-tag) |
| Test coverage (Sprint 7 emitters) | **20/20 PASS** |

**Verdict**: Proceed Wave 1 in parallel with OQ-9 decision; do not start Wave 2 until `v9.4.0-p3`.

---

## 2. Gate matrix

| Gate | Status | Evidence |
|------|--------|----------|
| G6–G10 | ✅ PASS | scripts + evidence files |
| G11 | 🟡 **12/14** | `gate11-k8s-demo.txt` 2026-07-09 |
| Tag v9.4.0-p3 | ⬜ BLOCKED | Constitution VIII + OQ-9 |

**Failures**: Step 10 OR-Tools schedule timeout; Step 11 approve (cascade).

---

## 3. Spec coverage

| Artifact | 015 | 016 | 017 | PRD |
|----------|-----|-----|-----|-----|
| Enterprise gates | ✅ | — | Phase 0 | §16 |
| Activity/EIB | — | ✅ Tier 1 | P0-04–06 | §7 |
| Priority 9 features | Phase 4/5 | — | Waves 1–3 | §16 |
| Copilot R1 | — | — | W1-01 ✅ | §7 |

---

## 4. Implementation status (codebase)

| Component | Status |
|-----------|--------|
| `ipe_shared/activity/emit.py` | ✅ |
| connector/cap/res emitters | ✅ |
| migration 038 file | ✅; apply ⬜ |
| Copilot R1 sidebar | ✅ 2026-07-09 |
| Odoo Config v2 | ⬜ |
| OTD service | ⬜ |

---

## 5. Risk register (from roadmap)

| Risk | Mitigation | Owner task |
|------|------------|------------|
| Gate 11 timeout | cap-svc CPU / port-forward | P0-02 |
| Single-dev bottleneck | Sequential waves | plan.md |
| ML accuracy | Hybrid fallback | W2-05/06 |
| NL misclassification | 0.85 threshold + preview | W3-01 |

---

## 6. Recommended order

1. P0-07 T730 migration  
2. P0-03 OQ-9 decision  
3. P0-08 tag (if unblocked)  
4. W1-02 Copilot smoke test  
5. W1-03–08 Wave 1 features  

---

*Analyze v1.0 — 2026-07-09*
