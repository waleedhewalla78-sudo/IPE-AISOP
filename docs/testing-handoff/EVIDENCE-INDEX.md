# v7.0.0 — Automated Evidence Index

All paths relative to repository root.

## Regression (P11)

| Artifact | Description |
|----------|-------------|
| `docs/final-regression-demo.txt` | Full demo 20/20 (2026-06-26) |
| `docs/final-regression-chaos.txt` | Chaos summary 6/6 |
| `docs/chaos/C1-nlp-kill.md` … `C6-post-chaos-regression.md` | Per-scenario chaos evidence |

## Quality gates

| Artifact | Description |
|----------|-------------|
| `docs/coverage-report-v7.md` | Per-service coverage ≥75% |
| `docs/speckit-final-p6.txt` | Speckit 162/162 closure |
| `docs/audit-final-score-v7.md` | Audit 100/100 documented |

## Earlier baselines

| Artifact | Description |
|----------|-------------|
| `docs/demo-run-report-wave3-live.txt` | Wave 3 demo 20/20 |
| `docs/k6-summary.md` | k6 smoke / load results |
| `docs/chaos/chaos-summary.md` | Chaos engineering overview |

## Re-run commands

```powershell
.\scripts\rel-demo-stack.ps1 -SkipBuild
.\scripts\run-full-demo.ps1 -ReportPath docs\final-regression-demo.txt
.\scripts\run-chaos-scenarios.ps1
```
