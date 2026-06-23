import { check, sleep } from "k6";
import http from "k6/http";
import { Rate, Trend } from "k6/metrics";

// Custom metrics for Phase 5-6 endpoints
const sopFailRate = new Rate("sop_failures");
const cogmFailRate = new Rate("cogm_failures");
const copqFailRate = new Rate("copq_failures");
const twinFailRate = new Rate("twin_failures");
const disruptFailRate = new Rate("disrupt_failures");
const sustainFailRate = new Rate("sustain_failures");
const qualityFailRate = new Rate("quality_failures");
const scnFailRate = new Rate("scn_failures");

const sopDuration = new Trend("sop_request_duration");
const cogmDuration = new Trend("cogm_request_duration");
const copqDuration = new Trend("copq_request_duration");
const twinDuration = new Trend("twin_request_duration");
const disruptDuration = new Trend("disrupt_request_duration");
const sustainDuration = new Trend("sustain_request_duration");
const qualityDuration = new Trend("quality_request_duration");
const scnDuration = new Trend("scn_request_duration");

// Service URLs (adjust ports to match docker-compose)
const BASE_DPE = __ENV.BASE_DPE || "http://localhost:8020";
const BASE_SUSTAIN = __ENV.BASE_SUSTAIN || "http://localhost:8012";
const BASE_QUALITY = __ENV.BASE_QUALITY || "http://localhost:8013";
const BASE_SCN = __ENV.BASE_SCN || "http://localhost:8014";
const BASE_NETWORK = __ENV.BASE_NETWORK || "http://localhost:8015";

const TENANT_ID = __ENV.TENANT_ID || "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11";
const JWT_TOKEN = __ENV.JWT_TOKEN || "";

const COMMON_HEADERS = {
    "Content-Type": "application/json",
    "X-Tenant-ID": TENANT_ID,
};
if (JWT_TOKEN) {
    COMMON_HEADERS["Authorization"] = `Bearer ${JWT_TOKEN}`;
}

export const options = {
    stages: [
        { duration: "10s", target: 10 },
        { duration: "30s", target: 50 },
        { duration: "10s", target: 10 },
        { duration: "10s", target: 0 },
    ],
    thresholds: {
        http_req_duration: ["p(95)<2000"],
        sop_failures: [{ threshold: "rate<0.1", abortOnFail: false }],
        cogm_failures: [{ threshold: "rate<0.1", abortOnFail: false }],
        twin_failures: [{ threshold: "rate<0.1", abortOnFail: false }],
    },
};

export default function () {
    // --- Phase 5: S&OP ---
    // S&OP forecast ingest
    let sopForecastRes = http.post(`${BASE_DPE}/api/v1/sop/forecast`, JSON.stringify({
        product_family: "Electronics",
        period_type: "weekly",
        period_start: "2026-01-06",
        period_end: "2026-01-13",
        forecast_qty: 500 + Math.floor(Math.random() * 200),
        confidence_pct: 0.8 + Math.random() * 0.15,
        source: "pipeline",
    }), { headers: COMMON_HEADERS });
    sopDuration.add(sopForecastRes.timings.duration);
    sopFailRate.add(sopForecastRes.status !== 200);
    check(sopForecastRes, { "sop forecast status 200": (r) => r.status === 200 });

    // S&OP solve
    let sopSolveRes = http.post(`${BASE_DPE}/api/v1/sop/solve`, JSON.stringify({
        demand: [
            { period_start: "2026-01-06", period_end: "2026-01-13", product_family: "A", forecast_qty: 100, confidence_pct: 0.8 },
            { period_start: "2026-01-13", period_end: "2026-01-20", product_family: "A", forecast_qty: 120, confidence_pct: 0.85 },
        ],
        capacity: [
            { period_start: "2026-01-06", period_end: "2026-01-13", work_center_group: "WC-A", capacity_hours: 168, capacity_qty: 100 },
            { period_start: "2026-01-13", period_end: "2026-01-20", work_center_group: "WC-A", capacity_hours: 168, capacity_qty: 120 },
        ],
        bottleneck_threshold_pct: 10.0,
    }), { headers: COMMON_HEADERS });
    sopDuration.add(sopSolveRes.timings.duration);
    check(sopSolveRes, { "sop solve status 200": (r) => r.status === 200 });

    // --- Phase 5: Cost Accounting ---
    // COGM
    let cogmRes = http.post(`${BASE_DPE}/api/v1/cost-accounting/cogm`, JSON.stringify({
        material_cost: 5000, labor_cost: 2000, energy_cost: 1000, overhead_cost: 500, quantity: 100,
    }), { headers: COMMON_HEADERS });
    cogmDuration.add(cogmRes.timings.duration);
    cogmFailRate.add(cogmRes.status !== 200);
    check(cogmRes, { "cogm status 200": (r) => r.status === 200 });

    // COPQ
    let copqRes = http.post(`${BASE_DPE}/api/v1/cost-accounting/copq`, JSON.stringify({
        total_quantity: 1000, defect_rate_pct: 5.0, rework_rate_pct: 2.0,
    }), { headers: COMMON_HEADERS });
    copqDuration.add(copqRes.timings.duration);
    copqFailRate.add(copqRes.status !== 200);
    check(copqRes, { "copq status 200": (r) => r.status === 200 });

    // --- Phase 5: Sustainability ---
    let sustainRes = http.post(`${BASE_SUSTAIN}/api/v1/sustainability/circularity-score`, JSON.stringify({
        product_id: `PROD-${Math.floor(Math.random() * 100)}`,
    }), { headers: COMMON_HEADERS });
    sustainDuration.add(sustainRes.timings.duration);
    sustainFailRate.add(sustainRes.status !== 200);
    check(sustainRes, { "sustainability status 200": (r) => r.status === 200 });

    // --- Phase 5: Quality ---
    let qualityRes = http.post(`${BASE_QUALITY}/api/v1/quality/spc/xbar`, JSON.stringify({
        measurements: [[10.1, 10.0, 9.9], [10.2, 10.1, 10.0], [10.0, 9.8, 10.1]],
    }), { headers: COMMON_HEADERS });
    qualityDuration.add(qualityRes.timings.duration);
    qualityFailRate.add(qualityRes.status !== 200);
    check(qualityRes, { "quality spc status 200": (r) => r.status === 200 });

    // --- Phase 5: SCN ---
    let scnRes = http.post(`${BASE_SCN}/api/v1/scn/supplier/score`, JSON.stringify({
        supplier_id: `SUP-${Math.floor(Math.random() * 10)}`,
    }), { headers: COMMON_HEADERS });
    scnDuration.add(scnRes.timings.duration);
    scnFailRate.add(scnRes.status !== 200);
    check(scnRes, { "scn score status 200": (r) => r.status === 200 });

    // --- Phase 6: Digital Twin BOM ---
    let twinRes = http.get(`${BASE_NETWORK}/api/v1/digital-twin/bom/MO-001`, { headers: COMMON_HEADERS });
    twinDuration.add(twinRes.timings.duration);
    twinFailRate.add(twinRes.status !== 200);
    check(twinRes, { "bom explosion status 200": (r) => r.status === 200 });

    // --- Phase 6: Disruption Simulation ---
    let disruptRes = http.post(`${BASE_NETWORK}/api/v1/digital-twin/disrupt`, JSON.stringify({
        disruption_type: "supplier_delay",
        source_id: "SUP-T2-001",
        delay_days: 7.0 + Math.random() * 14,
    }), { headers: COMMON_HEADERS });
    disruptDuration.add(disruptRes.timings.duration);
    disruptFailRate.add(disruptRes.status !== 200);
    check(disruptRes, { "disruption sim status 200": (r) => r.status === 200 });

    sleep(0.5);
}