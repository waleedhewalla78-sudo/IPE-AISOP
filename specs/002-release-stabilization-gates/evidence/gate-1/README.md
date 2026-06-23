# Gate 1 Test Evidence



**Date**: 2026-06-22  

**Feature**: 002-release-stabilization-gates  

**Status**: **PASSED**



## Results



| Suite | Result | Log |

|-------|--------|-----|

| shared | 126 passed, 12 skipped | shared.log |

| dpe-svc | 135 passed, 2 skipped | dpe-svc.log |

| mat-svc | 100 passed | mat-svc.log |

| cap-svc | 198 passed | cap-svc.log |

| fea-svc | 68 passed | fea-svc.log |

| frontend | 17/17 vitest + typecheck 0 errors | frontend.log |
| dpe-svc auth | 4/4 (test_auth.py, T062) | dpe-svc.log |

| (+ 10 more services) | see per-service logs | *.log |



## pytest collect-only



**700+** project test functions (exclude `.venv`) — see `run-all-tests.ps1` output in logs.



**Signed**: Gate 1 contract `contracts/gate-1-engineering.md`


