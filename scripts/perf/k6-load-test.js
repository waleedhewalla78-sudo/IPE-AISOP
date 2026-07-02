import http from "k6/http";
import { check, sleep } from "k6";
import { Rate, Trend } from "k6/metrics";

const BASE_URL = __ENV.BASE_URL || "http://localhost:8000";
const TOKEN = __ENV.TOKEN || "";
const TENANT_ID = __ENV.TENANT_ID || "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11";
const MAX_VUS = parseInt(__ENV.MAX_VUS || "10", 10);
const PROFILE = __ENV.K6_PROFILE || "r1-slo";

const ENDPOINT_PROFILES = {
  // R1 SLO baseline — fast read paths only (Release 2 outcomes excluded per Phase 1 gate)
  "r1-slo": [
    { weight: 50, method: "GET", path: "/api/v1/health", name: "Health Check", tag: "health" },
    { weight: 50, method: "GET", path: "/api/v1/auth/info", name: "Auth Info", tag: "auth" },
  ],
  // Full mix including analytics/resolution (stress profile — P95 SLO not expected on dev stack)
  full: [
    { weight: 25, method: "GET", path: "/api/v1/health", name: "Health Check", tag: "health" },
    { weight: 15, method: "GET", path: "/api/v1/auth/info", name: "Auth Info", tag: "auth" },
    { weight: 20, method: "GET", path: "/api/v1/resolution/scenarios", name: "Resolution Scenarios", tag: "resolution" },
    {
      weight: 15,
      method: "GET",
      path: `/api/v1/feasibility/queue?tenant_id=${TENANT_ID}`,
      name: "Feasibility Queue",
      tag: "feasibility",
    },
    {
      weight: 10,
      method: "GET",
      path: `/api/v1/outcomes/otd-baseline?tenant_id=${TENANT_ID}`,
      name: "OTD Baseline",
      tag: "outcomes",
    },
    {
      weight: 10,
      method: "GET",
      path: `/api/v1/outcomes/roi-metrics?tenant_id=${TENANT_ID}`,
      name: "ROI Metrics",
      tag: "outcomes",
    },
    {
      weight: 5,
      method: "GET",
      path: `/api/v1/feasibility/mdr?tenant_id=${TENANT_ID}`,
      name: "MDR Score",
      tag: "mdr",
    },
  ],
};

export const options = {
  stages: [
    { duration: "30s", target: 10 },
    { duration: "60s", target: MAX_VUS },
    { duration: "60s", target: MAX_VUS },
    { duration: "30s", target: 0 },
  ],
  thresholds: {
    http_req_duration: ["p(95)<500", "p(99)<2000"],
    http_req_failed: ["rate<0.05"],
  },
};

const errorRate = new Rate("errors");
const apiLatency = new Trend("api_latency");

export function setup() {
  if (TOKEN) {
    return { token: TOKEN };
  }
  const loginResp = http.post(
    `${BASE_URL}/api/v1/auth/login`,
    JSON.stringify({ email: "Ahmed@nour", password: "admin" }),
    { headers: { "Content-Type": "application/json" } },
  );
  if (loginResp.status !== 200) {
    throw new Error(`Login failed: ${loginResp.status} ${loginResp.body}`);
  }
  const body = loginResp.json();
  const token = body?.data?.access_token;
  if (!token) {
    throw new Error(`Login response missing access_token: ${loginResp.body}`);
  }
  return { token };
}

export default function (data) {
  const headers = {
    Authorization: `Bearer ${data.token}`,
    "Content-Type": "application/json",
    "X-Tenant-ID": TENANT_ID,
  };

  const endpoints = ENDPOINT_PROFILES[PROFILE] || ENDPOINT_PROFILES["r1-slo"];

  const total = endpoints.reduce((s, e) => s + e.weight, 0);
  let pick = Math.random() * total;
  let endpoint = endpoints[0];
  for (const ep of endpoints) {
    pick -= ep.weight;
    if (pick <= 0) {
      endpoint = ep;
      break;
    }
  }
  const resp = http.request(endpoint.method, `${BASE_URL}${endpoint.path}`, null, {
    headers,
    tags: { endpoint: endpoint.tag || "other" },
  });

  check(resp, {
    [`${endpoint.name} is 200`]: (r) => r.status === 200,
    [`${endpoint.name} under 500ms`]: (r) => r.timings.duration < 500,
  });

  errorRate.add(resp.status !== 200);
  apiLatency.add(resp.timings.duration);
  sleep(0.25);
}

function _durationMs(data, key) {
  const v = data.metrics.http_req_duration?.values || {};
  if (key === "p(50)") return v.med ?? v["p(50)"];
  return v[key];
}

export function handleSummary(data) {
  const duration = data.metrics.http_req_duration?.values || {};
  const errors = data.metrics.errors?.values?.rate ?? 0;
  const failRate = data.metrics.http_req_failed?.values?.rate ?? 0;
  const count = data.metrics.http_reqs?.values?.count ?? 0;
  const p50 = _durationMs(data, "p(50)");
  const p95 = _durationMs(data, "p(95)");
  const p99 = _durationMs(data, "p(99)");

  console.log("\n=== Performance Summary ===");
  console.log(`Requests: ${count}`);
  console.log(`P50: ${p50 ?? "n/a"}ms`);
  console.log(`P95: ${p95 ?? "n/a"}ms`);
  console.log(`P99: ${p99 ?? "n/a"}ms`);
  console.log(`Errors: ${(errors * 100).toFixed(2)}%`);
  console.log(`HTTP fail rate: ${(failRate * 100).toFixed(2)}%`);
  console.log(`Max VUs: ${MAX_VUS}`);
  console.log(`Profile: ${PROFILE}`);

  return {
    stdout: textSummary(data),
    "docs/qa/k6-baseline-v9.2.0.json": JSON.stringify(data, null, 2),
  };
}

function textSummary(data) {
  const p50 = _durationMs(data, "p(50)");
  const p95 = _durationMs(data, "p(95)");
  const p99 = _durationMs(data, "p(99)");
  return [
    "=== IPE k6 Baseline ===",
    `requests: ${data.metrics.http_reqs?.values?.count ?? 0}`,
    `p50_ms: ${p50 ?? "n/a"}`,
    `p95_ms: ${p95 ?? "n/a"}`,
    `p99_ms: ${p99 ?? "n/a"}`,
    `error_rate: ${((data.metrics.errors?.values?.rate ?? 0) * 100).toFixed(2)}%`,
    `http_fail_rate: ${((data.metrics.http_req_failed?.values?.rate ?? 0) * 100).toFixed(2)}%`,
    `max_vus: ${MAX_VUS}`,
    `profile: ${PROFILE}`,
  ].join("\n");
}
