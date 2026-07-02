import http from "k6/http";
import { check, sleep } from "k6";
import { Rate, Trend } from "k6/metrics";

const BASE_URL = __ENV.BASE_URL || "http://localhost:8000";
const TOKEN = __ENV.TOKEN || "";

export const options = {
  stages: [
    { duration: "30s", target: 10 },
    { duration: "60s", target: 50 },
    { duration: "30s", target: 100 },
    { duration: "60s", target: 50 },
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
  };

  const endpoints = [
    {
      method: "GET",
      path: "/api/v1/feasibility/queue?tenant_id=startrans",
      name: "Feasibility Queue",
    },
    {
      method: "GET",
      path: "/api/v1/feasibility/mdr?tenant_id=startrans",
      name: "MDR Score",
    },
    { method: "GET", path: "/api/v1/resolution/scenarios", name: "Resolution Scenarios" },
    {
      method: "GET",
      path: "/api/v1/outcomes/otd-baseline?tenant_id=startrans",
      name: "OTD Baseline",
    },
    {
      method: "GET",
      path: "/api/v1/outcomes/roi-metrics?tenant_id=startrans",
      name: "ROI Metrics",
    },
    { method: "GET", path: "/api/v1/auth/info", name: "Auth Info" },
    { method: "GET", path: "/api/v1/health", name: "Health Check" },
  ];

  const endpoint = endpoints[Math.floor(Math.random() * endpoints.length)];
  const resp = http.request(endpoint.method, `${BASE_URL}${endpoint.path}`, null, { headers });

  check(resp, {
    [`${endpoint.name} is 200`]: (r) => r.status === 200,
    [`${endpoint.name} under 500ms`]: (r) => r.timings.duration < 500,
  });

  errorRate.add(resp.status !== 200);
  apiLatency.add(resp.timings.duration);
  sleep(0.1);
}

export function handleSummary(data) {
  const duration = data.metrics.http_req_duration?.values || {};
  const errors = data.metrics.errors?.values?.rate ?? 0;
  const count = data.metrics.http_reqs?.values?.count ?? 0;

  console.log("\n=== Performance Summary ===");
  console.log(`Requests: ${count}`);
  console.log(`P50: ${duration["p(50)"] ?? "n/a"}ms`);
  console.log(`P95: ${duration["p(95)"] ?? "n/a"}ms`);
  console.log(`P99: ${duration["p(99)"] ?? "n/a"}ms`);
  console.log(`Errors: ${(errors * 100).toFixed(2)}%`);

  return {
    stdout: textSummary(data),
    "docs/qa/k6-baseline.json": JSON.stringify(data, null, 2),
  };
}

function textSummary(data) {
  const duration = data.metrics.http_req_duration?.values || {};
  return [
    "=== IPE k6 Baseline ===",
    `requests: ${data.metrics.http_reqs?.values?.count ?? 0}`,
    `p50_ms: ${duration["p(50)"] ?? "n/a"}`,
    `p95_ms: ${duration["p(95)"] ?? "n/a"}`,
    `p99_ms: ${duration["p(99)"] ?? "n/a"}`,
    `error_rate: ${((data.metrics.errors?.values?.rate ?? 0) * 100).toFixed(2)}%`,
  ].join("\n");
}
