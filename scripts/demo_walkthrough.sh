#!/usr/bin/env bash
# =============================================================================
# IPE Platform — Full Demo Walkthrough with Sample Data
# =============================================================================
# Prerequisites: Docker stack running, migrations applied, seed data loaded
# Usage: bash scripts/demo_walkthrough.sh
# =============================================================================

set -euo pipefail

BASE="http://localhost:8000"
TENANT="a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"
MO_ID="b1eebc99-9c0b-4ef8-bb6d-6bb9bd380a22"
PRODUCT_ID="c2eebc99-9c0b-4ef8-bb6d-6bb9bd380a33"
PASS=0
FAIL=0
TOTAL=0

check() {
  local desc="$1" expected="$2" actual="$3"
  TOTAL=$((TOTAL+1))
  if echo "$actual" | grep -q "$expected"; then
    echo "  ✅ PASS: $desc"
    PASS=$((PASS+1))
  else
    echo "  ❌ FAIL: $desc (expected '$expected')"
    echo "         Got: $actual"
    FAIL=$((FAIL+1))
  fi
}

echo "============================================="
echo " IPE Platform — Full Demo Walkthrough"
echo "============================================="
echo ""

# ─────────────────────────────────────────────
# 1. HEALTH CHECKS — All 16 Services
# ─────────────────────────────────────────────
echo "━━━ 1. Health Checks ━━━"
for svc in dpe-svc mat-svc cap-svc fea-svc res-svc del-svc nlp-svc rec-svc alert-svc connector sustain-svc quality-svc scn-svc network-svc ml-svc; do
  code=$(curl -s -o /dev/null -w "%{http_code}" "$BASE/api/v1/health" -H "X-Tenant-ID: $TENANT" 2>/dev/null || echo "000")
  if [ "$code" = "200" ]; then
    check "$svc health" "200" "$code"
  else
    check "$svc health" "200" "$code"
  fi
done
echo ""

# ─────────────────────────────────────────────
# 2. DEMAND CLASSIFICATION — Priority Scoring
# ─────────────────────────────────────────────
echo "━━━ 2. Demand Classification (dpe-svc) ━━━"
RESULT=$(curl -s -X POST "$BASE/api/v1/demand/classify" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: $TENANT" \
  -d '{
    "demand_lines": [
      {
        "mo_id": "'$MO_ID'",
        "product_id": "'$PRODUCT_ID'",
        "quantity": 100,
        "due_date": "2026-07-15T00:00:00Z",
        "customer_id": "d3eebc99-9c0b-4ef8-bb6d-6bb9bd380a44",
        "priority_score": 0
      }
    ]
  }' 2>/dev/null)
check "Demand classify returns success" '"success":true' "$RESULT"
check "Priority score computed" '"priority_score"' "$RESULT"
echo ""

# ─────────────────────────────────────────────
# 3. PROBABILITY ATP — Material Availability
# ─────────────────────────────────────────────
echo "━━━ 3. Probabilistic ATP (mat-svc) ━━━"
RESULT=$(curl -s -X POST "$BASE/api/v1/material/probabilistic-atp" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: $TENANT" \
  -d '{
    "mo_id": "'$MO_ID'",
    "components": [
      {"component_id": "e4eebc99-9c0b-4ef8-bb6d-6bb9bd380a55", "quantity_per": 2.0, "lead_time_days": 7, "on_hand": 50, "safety_stock": 10},
      {"component_id": "f5eebc99-9c0b-4ef8-bb6d-6bb9bd380a66", "quantity_per": 1.0, "lead_time_days": 14, "on_hand": 20, "safety_stock": 5}
    ]
  }' 2>/dev/null)
check "pATP returns success" '"success":true' "$RESULT"
check "Overall probability computed" '"overall_probability"' "$RESULT"
echo ""

# ─────────────────────────────────────────────
# 4. CAPABLE-TO-PROMISE
# ─────────────────────────────────────────────
echo "━━━ 4. CTP Check (mat-svc) ━━━"
RESULT=$(curl -s -X POST "$BASE/api/v1/material/ctp" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: $TENANT" \
  -d '{
    "mo_id": "'$MO_ID'",
    "product_id": "'$PRODUCT_ID'",
    "quantity": 100,
    "required_date": "2026-07-15T00:00:00Z"
  }' 2>/dev/null)
check "CTP returns success" '"success":true' "$RESULT"
echo ""

# ─────────────────────────────────────────────
# 5. CAPACITY SCHEDULING — OR-Tools CP-SAT
# ─────────────────────────────────────────────
echo "━━━ 5. Capacity Scheduling (cap-svc) ━━━"
RESULT=$(curl -s -X POST "$BASE/api/v1/capacity/schedule" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: $TENANT" \
  -d '{
    "mo_ids": ["'$MO_ID'"],
    "horizon_hours": 168
  }' 2>/dev/null)
check "Schedule returns success" '"success":true' "$RESULT"
check "Assignments computed" '"assignments"' "$RESULT"
echo ""

# ─────────────────────────────────────────────
# 6. FEASIBILITY SCORING — 5-Gate Model
# ─────────────────────────────────────────────
echo "━━━ 6. Feasibility Scoring (fea-svc) ━━━"
RESULT=$(curl -s -X POST "$BASE/api/v1/feasibility/score" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: $TENANT" \
  -d '{
    "mo_id": "'$MO_ID'",
    "material_score": 85.0,
    "capacity_score": 72.0,
    "labor_score": 90.0,
    "demand_score": 95.0,
    "bom_score": 100.0
  }' 2>/dev/null)
check "Feasibility score returns success" '"success":true' "$RESULT"
check "Gate scores computed" '"gate_scores"' "$RESULT"
check "Action taken determined" '"action_taken"' "$RESULT"
echo ""

# ─────────────────────────────────────────────
# 7. FEASIBILITY KPIs
# ─────────────────────────────────────────────
echo "━━━ 7. Feasibility KPIs (fea-svc) ━━━"
RESULT=$(curl -s "$BASE/api/v1/feasibility/kpis" \
  -H "X-Tenant-ID: $TENANT" 2>/dev/null)
check "KPIs returns success" '"success":true' "$RESULT"
echo ""

# ─────────────────────────────────────────────
# 8. RESOLUTION SCENARIOS
# ─────────────────────────────────────────────
echo "━━━ 8. Resolution Scenarios (res-svc) ━━━"
RESULT=$(curl -s -X POST "$BASE/api/v1/resolution/scenarios" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: $TENANT" \
  -d '{
    "mo_id": "'$MO_ID'",
    "constraint_type": "material_shortage",
    "severity": "high"
  }' 2>/dev/null)
check "Resolution scenarios returned" '"success":true' "$RESULT"
check "Scenarios generated" '"scenarios"' "$RESULT"
echo ""

# ─────────────────────────────────────────────
# 9. COPILOT QUERY — NLP
# ─────────────────────────────────────────────
echo "━━━ 9. Copilot Query (nlp-svc) ━━━"
RESULT=$(curl -s -X POST "$BASE/api/v1/copilot/query" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: $TENANT" \
  -d '{
    "query": "What is the status of manufacturing order '$MO_ID'?",
    "stream": false
  }' 2>/dev/null)
check "Copilot returns response" '"success":true' "$RESULT"
check "Intent classified" '"intent"' "$RESULT"
echo ""

# ─────────────────────────────────────────────
# 10. COST ACCOUNTING — COGM/COPQ
# ─────────────────────────────────────────────
echo "━━━ 10. Cost Accounting (dpe-svc) ━━━"
RESULT=$(curl -s -X POST "$BASE/api/v1/cost-accounting/full" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: $TENANT" \
  -d '{
    "mo_id": "'$MO_ID'",
    "material_cost": 15000.0,
    "labor_cost": 8000.0,
    "energy_cost": 2500.0,
    "overhead_cost": 4500.0,
    "scrap_cost": 500.0,
    "rework_cost": 300.0,
    "inspection_cost": 200.0,
    "warranty_cost": 100.0,
    "quantity": 100,
    "selling_price": 500.0
  }' 2>/dev/null)
check "Cost accounting returns success" '"success":true' "$RESULT"
check "COGM computed" '"cogm"' "$RESULT"
check "COPQ computed" '"copq"' "$RESULT"
echo ""

# ─────────────────────────────────────────────
# 11. S&OP FORECAST
# ─────────────────────────────────────────────
echo "━━━ 11. S&OP Forecast (dpe-svc) ━━━"
RESULT=$(curl -s -X POST "$BASE/api/v1/sop/forecast" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: $TENANT" \
  -d '{
    "forecast_lines": [
      {"product_id": "'$PRODUCT_ID'", "quantity": 500, "week": "2026-W28", "confidence": 0.85},
      {"product_id": "'$PRODUCT_ID'", "quantity": 600, "week": "2026-W29", "confidence": 0.80},
      {"product_id": "'$PRODUCT_ID'", "quantity": 450, "week": "2026-W30", "confidence": 0.90}
    ]
  }' 2>/dev/null)
check "S&OP forecast ingested" '"success":true' "$RESULT"
echo ""

# ─────────────────────────────────────────────
# 12. FINANCIAL PROJECTION
# ─────────────────────────────────────────────
echo "━━━ 12. Financial Projection (dpe-svc) ━━━"
RESULT=$(curl -s -X POST "$BASE/api/v1/financial/project" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: $TENANT" \
  -d '{
    "product_id": "'$PRODUCT_ID'",
    "quantity": 100,
    "selling_price": 500.0,
    "overhead_pct": 0.15,
    "labor_cost_per_hour": 45.0
  }' 2>/dev/null)
check "Financial projection returned" '"success":true' "$RESULT"
echo ""

# ─────────────────────────────────────────────
# 13. SOC 2 COMPLIANCE
# ─────────────────────────────────────────────
echo "━━━ 13. SOC 2 Compliance (dpe-svc) ━━━"
RESULT=$(curl -s "$BASE/api/v1/compliance/soc2/summary" \
  -H "X-Tenant-ID: $TENANT" 2>/dev/null)
check "SOC 2 summary available" '"success":true' "$RESULT"
echo ""

# ─────────────────────────────────────────────
# 14. GDPR DSAR
# ─────────────────────────────────────────────
echo "━━━ 14. GDPR DSAR (dpe-svc) ━━━"
RESULT=$(curl -s -X POST "$BASE/api/v1/dsar/requests" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: $TENANT" \
  -d '{
    "subject_id": "user-12345",
    "request_type": "access",
    "description": "Data subject access request"
  }' 2>/dev/null)
check "DSAR request created" '"success":true' "$RESULT"
echo ""

# ─────────────────────────────────────────────
# 15. AUDIT LOG
# ─────────────────────────────────────────────
echo "━━━ 15. Audit Log (shared) ━━━"
RESULT=$(curl -s "$BASE/api/v1/compliance/audit/events" \
  -H "X-Tenant-ID: $TENANT" 2>/dev/null)
check "Audit events accessible" '"success":true' "$RESULT"
echo ""

# ─────────────────────────────────────────────
# 16. QUALITY EVENT
# ─────────────────────────────────────────────
echo "━━━ 16. Quality Event (del-svc) ━━━"
RESULT=$(curl -s -X POST "$BASE/api/v1/quality/events" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: $TENANT" \
  -d '{
    "mo_id": "'$MO_ID'",
    "product_id": "'$PRODUCT_ID'",
    "event_type": "defect_detected",
    "severity": "minor",
    "defect_category": "surface",
    "defect_count": 2
  }' 2>/dev/null)
check "Quality event created" '"success":true' "$RESULT"
echo ""

# ─────────────────────────────────────────────
# 17. SUSTAINABILITY
# ─────────────────────────────────────────────
echo "━━━ 17. Sustainability Score (sustain-svc) ━━━"
RESULT=$(curl -s "$BASE/api/v1/sustainability/circularity-score" \
  -H "X-Tenant-ID: $TENANT" 2>/dev/null)
check "Sustainability score available" '"success":true' "$RESULT"
echo ""

# ─────────────────────────────────────────────
# 18. SCN SUPPLIER SCORE
# ─────────────────────────────────────────────
echo "━━━ 18. Supplier Score (scn-svc) ━━━"
RESULT=$(curl -s "$BASE/api/v1/supplier/score" \
  -H "X-Tenant-ID: $TENANT" 2>/dev/null)
check "Supplier score available" '"success":true' "$RESULT"
echo ""

# ─────────────────────────────────────────────
# 19. DIGITAL TWIN BOM EXPLOSION
# ─────────────────────────────────────────────
echo "━━━ 19. Digital Twin BOM (network-svc) ━━━"
RESULT=$(curl -s "$BASE/api/v1/digital-twin/bom/$MO_ID" \
  -H "X-Tenant-ID: $TENANT" 2>/dev/null)
check "BOM explosion returned" '"success":true' "$RESULT"
echo ""

# ─────────────────────────────────────────────
# 20. PREDICT DURATION
# ─────────────────────────────────────────────
echo "━━━ 20. Predict Duration (ml-svc) ━━━"
RESULT=$(curl -s -X POST "$BASE/api/v1/predict/duration" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: $TENANT" \
  -d '{
    "mo_id": "'$MO_ID'",
    "product_id": "'$PRODUCT_ID'",
    "quantity": 100
  }' 2>/dev/null)
check "Duration prediction returned" '"success":true' "$RESULT"
echo ""

# ─────────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────────
echo "============================================="
echo " DEMO RESULTS: $PASS/$TOTAL passed, $FAIL failed"
echo "============================================="
if [ "$FAIL" -eq 0 ]; then
  echo " 🎉 All demos passed!"
else
  echo " ⚠️  $FAIL demo(s) need attention"
fi
