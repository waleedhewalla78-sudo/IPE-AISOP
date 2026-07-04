# GitHub Issues — Phase 3 Pending Tasks

**Repo**: https://github.com/waleedhewalla78-sudo/IPE-AISOP  
**Generated**: 2026-07-04 (`/speckit.taskstoissues`)  
**Label**: `enterprise-phase-3` (create label if missing)

Create with:

```powershell
cd E:\AISOP\ipe
gh label create enterprise-phase-3 --description "Enterprise Phase 3 — K8s/compliance" 2>$null
```

| Task | Title | Body summary |
|------|-------|--------------|
| T150 | T150: Gate 6 Helm lint and template | Run `scripts/k8s/verify-gate6.sh` |
| T151 | T151: Gate 7 kind deploy health | `scripts/k8s/deploy-kind.sh` + `verify-k8s.sh` |
| T152 | T152: Gate 8 Compose-K8s parity | `scripts/k8s/test-compose-k8s-parity.py` |
| T153 | T153: Gate 9 HPA smoke test | CPU load → scale-up on prod values |
| T155 | T155: Gate 11 R1 demo on K8s | 14/14 via ingress |
| T156 | T156: k6 SLO on K8s ingress | P95 < 500ms |
| T157 | T157: Tag v9.4.0-p3 | After Gates 6–11 PASS |
| T090a | T090a: GDPR export hardening | `dpe-svc/dsar.py` |
| T091a | T091a: GDPR erasure jobs | Retention purge |
| T092 | T092: WCAG 2.1 AA audit | Core R1 screens |
| T093 | T093: SOC 2 Type I gap doc | `docs/compliance/` |
| T094 | T094: k6 500 VU CI job | Staging workflow |
| T097 | T097: API v2 Kong routes | Version prefix pattern |

**Completed (no issue needed):** T154 Gate 10 — `tests/test_erp_scaffolds.py`  
**Completed:** T099 Track B, T140 K8s guide, T095a registry, **T150 Gate 6**, **T162 issues #12-24**

## Created issues (2026-07-04)

| Task | Issue |
|------|-------|
| T150 | https://github.com/waleedhewalla78-sudo/IPE-AISOP/issues/12 |
| T151 | https://github.com/waleedhewalla78-sudo/IPE-AISOP/issues/13 |
| T152 | https://github.com/waleedhewalla78-sudo/IPE-AISOP/issues/14 |
| T153 | https://github.com/waleedhewalla78-sudo/IPE-AISOP/issues/15 |
| T155 | https://github.com/waleedhewalla78-sudo/IPE-AISOP/issues/16 |
| T156 | https://github.com/waleedhewalla78-sudo/IPE-AISOP/issues/17 |
| T157 | https://github.com/waleedhewalla78-sudo/IPE-AISOP/issues/18 |
| T090a | https://github.com/waleedhewalla78-sudo/IPE-AISOP/issues/19 |
| T091a | https://github.com/waleedhewalla78-sudo/IPE-AISOP/issues/20 |
| T092 | https://github.com/waleedhewalla78-sudo/IPE-AISOP/issues/21 |
| T093 | https://github.com/waleedhewalla78-sudo/IPE-AISOP/issues/22 |
| T094 | https://github.com/waleedhewalla78-sudo/IPE-AISOP/issues/23 |
| T097 | https://github.com/waleedhewalla78-sudo/IPE-AISOP/issues/24 |
