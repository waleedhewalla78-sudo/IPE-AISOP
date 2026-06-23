import { check, sleep } from "k6";
import http from "k6/http";
import { Rate, Trend, Counter, Gauge } from "k6/metrics";

// --- Custom metrics ---
const demandFailRate = new Rate("demand_failures");
const matFailRate = new Rate("mat_failures");
const capFailRate = new Rate("cap_failures");
const feaFailRate = new Rate("fea_failures");
const recFailRate = new Rate("rec_failures");
const nlpFailRate = new Rate("nlp_failures");

const demandDuration = new Trend("demand_request_duration");
const matDuration = new Trend("mat_request_duration");
const capDuration = new Trend("cap_request_duration");
const feaDuration = new Trend("fea_request_duration");
const recDuration = new Trend("rec_request_duration");
const nlpDuration = new Trend("nlp_request_duration");

const activeVUs = new Gauge("active_vus");
const totalRequests = new Counter("total_requests");

// --- Service endpoints ---
const BASE_DEMAND = __ENV.BASE_DEMAND || "http://localhost:8012";
const BASE_MATERIAL = __ENV.BASE_MATERIAL || "http://localhost:8002";
const BASE_CAPACITY = __ENV.BASE_CAPACITY || "http://localhost:8003";
const BASE_FEASIBILITY = __ENV.BASE_FEASIBILITY || "http://localhost:8004";
const BASE_RESOLUTION = __ENV.BASE_RESOLUTION || "http://localhost:8005";
const BASE_DELAY = __ENV.BASE_DELAY || "http://localhost:8006";
const BASE_NLP = __ENV.BASE_NLP || "http://localhost:8007";
const BASE_RECOMMENDATION = __ENV.BASE_RECOMMENDATION || "http://localhost:8008";
const BASE_ALERT = __ENV.BASE_ALERT || "http://localhost:8009";
const BASE_CONNECTOR = __ENV.BASE_CONNECTOR || "http://localhost:8010";

const TENANT_ID = __ENV.TENANT_ID || "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11";

const COMMON_HEADERS = {
    "Content-Type": "application/json",
    "X-Tenant-ID": TENANT_ID,
};

// --- Test UUIDs (valid format) ---
const DEMAND_LINES = [
    "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a01",
    "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a02",
    "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a03",
    "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a04",
    "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a05",
];
const MO_IDS = [
    "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
    "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12",
    "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a13",
    "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a14",
    "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a15",
];

// --- Scenarios ---
export const options = {
    scenarios: {
        // Smoke test: 1 VU for 30s to verify endpoints work
        smoke: {
            executor: "constant-vus",
            vus: 1,
            duration: "30s",
            gracefulStop: "5s",
            tags: { scenario: "smoke" },
        },
        // Ramp-up load test: 0 → 200 VUs over 2 min, hold for 3 min
        ramp_up: {
            executor: "ramping-vus",
            startVUs: 0,
            stages: [
                { duration: "30s", target: 10 },
                { duration: "30s", target: 50 },
                { duration: "30s", target: 100 },
                { duration: "30s", target: 200 },
                { duration: "2m", target: 200 },
                { duration: "30s", target: 0 },
            ],
            gracefulRampDown: "15s",
            tags: { scenario: "ramp_up" },
        },
        // Constant load: 200 VUs for 5 min
        sustained: {
            executor: "constant-vus",
            vus: 200,
            duration: "5m",
            gracefulStop: "30s",
            tags: { scenario: "sustained" },
        },
    },
    thresholds: {
        http_req_duration: ["p(95)<5000"],
        http_req_failed: ["rate<0.01"],
        demand_failures: ["rate<0.02"],
        mat_failures: ["rate<0.02"],
        cap_failures: ["rate<0.02"],
        fea_failures: ["rate<0.02"],
        demand_request_duration: ["p(95)<3000"],
        mat_request_duration: ["p(95)<3000"],
        cap_request_duration: ["p(95)<5000"],
        fea_request_duration: ["p(95)<3000"],
    },
};

function recordResult(res, failRate, trend, label) {
    trend.add(res.timings.duration);
    failRate.add(res.status < 200 || res.status >= 400);
    totalRequests.add(1);
    check(res, {
        [`${label} status 2xx`]: (r) => r.status >= 200 && r.status < 300,
        [`${label} has data`]: (r) => {
            try { return JSON.parse(r.body).success === true; }
            catch { return false; }
        },
    });
}

export default function () {
    activeVUs.add(1);
    const idx = Math.floor(Math.random() * DEMAND_LINES.length);
    const moIdx = Math.floor(Math.random() * MO_IDS.length);

    // --- 1. Demand classify (lightweight) ---
    const demandPayload = JSON.stringify({ demand_line_ids: [DEMAND_LINES[idx]] });
    const demandRes = http.post(
        `${BASE_DEMAND}/api/v1/demand/classify`,
        demandPayload,
        { headers: COMMON_HEADERS, timeout: "10s" }
    );
    recordResult(demandRes, demandFailRate, demandDuration, "demand_classify");

    sleep(Math.random() * 0.5);

    // --- 2. Material probabilistic ATP (Monte Carlo - compute heavy) ---
    const matPayload = JSON.stringify({
        mo: { id: MO_IDS[moIdx], product_id: `PROD-${idx + 1}`, qty: 100 },
        components: [
            { component_id: "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a20", quantity_per: 10 },
            { component_id: "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a21", quantity_per: 5 },
        ],
        required_start: "2026-06-15T00:00:00Z",
    });
    const matRes = http.post(
        `${BASE_MATERIAL}/api/v1/material/probabilistic-atp`,
        matPayload,
        { headers: COMMON_HEADERS, timeout: "30s" }
    );
    recordResult(matRes, matFailRate, matDuration, "mat_probabilistic_atp");

    sleep(Math.random() * 0.5);

    // --- 3. Capacity schedule (OR-Tools solver - compute heavy) ---
    const capPayload = JSON.stringify({
        mo_ids: [MO_IDS[moIdx]],
        horizon_hours: 168,
    });
    const capRes = http.post(
        `${BASE_CAPACITY}/api/v1/capacity/schedule`,
        capPayload,
        { headers: COMMON_HEADERS, timeout: "60s" }
    );
    recordResult(capRes, capFailRate, capDuration, "cap_schedule");

    sleep(Math.random() * 0.5);

    // --- 4. Feasibility score ---
    const feaPayload = JSON.stringify({
        mo_id: MO_IDS[moIdx],
        gate_scores: {
            g1_demand: 85,
            g2_bom: 90,
            g3_material: 75,
            g4_capacity: 80,
            g5_labor: 95,
        },
        autonomy_mode: "shadow",
    });
    const feaRes = http.post(
        `${BASE_FEASIBILITY}/api/v1/feasibility/score`,
        feaPayload,
        { headers: COMMON_HEADERS, timeout: "10s" }
    );
    recordResult(feaRes, feaFailRate, feaDuration, "fea_score");

    sleep(Math.random() * 0.5);

    // --- 5. Resolution scenarios ---
    const recPayload = JSON.stringify({
        mo_id: MO_IDS[moIdx],
        constraints: [
            { type: "material_shortage", severity: 0.8, value: 200 },
        ],
    });
    const recRes = http.post(
        `${BASE_RESOLUTION}/api/v1/resolution/scenarios`,
        recPayload,
        { headers: COMMON_HEADERS, timeout: "10s" }
    );
    recordResult(recRes, recFailRate, recDuration, "resolution_scenarios");

    sleep(Math.random() * 0.5);

    // --- 6. NLP copilot ---
    const nlpPayload = JSON.stringify({
        query: "What is the material status for MO " + MO_IDS[moIdx].substring(0, 8) + "?",
        stream: false,
    });
    const nlpRes = http.post(
        `${BASE_NLP}/api/v1/copilot/query`,
        nlpPayload,
        { headers: COMMON_HEADERS, timeout: "15s" }
    );
    recordResult(nlpRes, nlpFailRate, nlpDuration, "nlp_copilot");

    activeVUs.add(-1);
    sleep(Math.random() * 1);
}

export function handleSummary(data) {
    const summary = {
        root: data,
        scenarios: Object.keys(data.scenarios || {}),
        p95_demand: data.metrics?.demand_request_duration?.values?.["p(95)"] || "N/A",
        p95_mat: data.metrics?.mat_request_duration?.values?.["p(95)"] || "N/A",
        p95_cap: data.metrics?.cap_request_duration?.values?.["p(95)"] || "N/A",
        p95_fea: data.metrics?.fea_request_duration?.values?.["p(95)"] || "N/A",
        pass: true,
    };

    const checks = data.root?.checks || {};
    for (const [name, val] of Object.entries(checks)) {
        if (val.fails > 0) {
            summary.pass = false;
            break;
        }
    }

    return {
        stdout: `\n=== IPE Load Test Summary ===\n` +
            `Scenarios: ${summary.scenarios.join(", ")}\n` +
            `p95 demand: ${summary.p95_demand}ms\n` +
            `p95 material: ${summary.p95_mat}ms\n` +
            `p95 capacity: ${summary.p95_cap}ms\n` +
            `p95 feasibility: ${summary.p95_fea}ms\n` +
            `PASS: ${summary.pass}\n`,
        "load-test-report.json": JSON.stringify(summary, null, 2),
    };
}