# R4 evidence placeholder — run scripts to populate

| Artifact | Generator |
|----------|-----------|
| `sap-sandbox-report.txt` | `.\scripts\test-sap-sandbox.ps1` |
| `d365-sandbox-report.txt` | `.\scripts\test-d365-sandbox.ps1` |
| `k6-200vu-summary.txt` | `.\scripts\run-k6-200vu.ps1` |
| `airflow-verify-report.txt` | `.\scripts\verify-airflow.ps1` |
| `chaos-recovery-metrics.txt` | `.\infrastructure\chaos\collect-evidence.ps1` |

Attach completed reports before `git tag v1.0.0`.
