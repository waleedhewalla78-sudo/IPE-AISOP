# Star Trans on-call (BATCH2-1 stub)

Hypercare weeks 10–13 are owned by BATCH2-5. This file only registers the
tenant on the rotation list.

| Window | Coverage |
|--------|----------|
| Lab | Diligent engineering, Cairo business hours |
| Production hypercare | TBD BATCH2-5 |

PagerDuty/Opsgenie: **not wired**. Sev 1/2 pages must not be claimed operational.

Alert intents (Prometheus rules in `infrastructure/monitoring/prometheus/alerts-star-trans.yml`):

- DQ score &lt; 70 (metric may be absent on lab → alert dormant)
- Feasibility recalc &gt; 30s
- Copilot latency &gt; 8s
