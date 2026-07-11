# Planning Intelligence UAT Results

**Date:** 2026-07-11
**BaseUrl:** http://localhost:8000

| Step | Status | Detail |
|------|--------|--------|
| UAT-4 | PARTIAL | Some health endpoints failed (see above) |
| UAT-5-login | PASS | JWT obtained via Kong |
| UAT-5 | PASS | Kong planning API contracts OK |
| UAT-6 | PASS | products_classified=7 |
| UAT-7 | PASS | calculate accepted |
| UAT-8 | PASS | FSM transitions + invalid reject |
| UAT-9 | PASS | consensus calculate version=6b6ec7d9-871b-4873-a273-ab8fccd8419e |
| UAT-10 | PARTIAL | Live copilot chat timed out; planning tools covered by unit tests 22/22 |
| UAT-11 | PASS | best_fit product=686a3055-9a20-4824-b257-0f88b2733c63 model=ses |
| UAT-12 | PASS | segment product 686a3055-9a20-4824-b257-0f88b2733c63 SL=97.0 safety-stock linked |

PASS=8 PARTIAL=2 FAIL=0
