// k6-slo.js — Service Level Objective baseline (Phase 2 close)
// Purpose: Measure real service latency under NORMAL load (within Kong 500 req/min)
// Usage: k6 run scripts/perf/k6-slo.js --out json=docs/qa/k6-slo-baseline.json
// SLO: P95 < 500ms, error rate < 5%

import http from "k6/http";
import { check, sleep } from "k6";
import { Rate, Trend } from "k6/metrics";

const errorRate = new Rate("errors");
const apiLatency = new Trend("api_latency");

const KONG_URL = __ENV.KONG_URL || __ENV.BASE_URL || "http://localhost:8000";
const KEYCLOAK_URL = __ENV.KEYCLOAK_URL || "http://localhost:8180";
const AUTH_MODE = __ENV.AUTH_MODE || "keycloak";
const TENANT_ID = __ENV.TENANT_ID || "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11";

export const options = {
  stages: [
    { duration: "30s", target: 5 },
    { duration: "60s", target: 5 },
    { duration: "30s", target: 8 },
    { duration: "60s", target: 8 },
    { duration: "20s", target: 0 },
  ],
  thresholds: {
    errors: ["rate<0.05"],
    api_latency: ["p(95)<500"],
    "http_req_duration{api:feasibility}": ["p(95)<500"],
    "http_req_duration{api:health}": ["p(95)<500"],
  },
};

const ENDPOINTS = [
  { path: "/api/v1/health", tag: "health", weight: 4, method: "GET" },
  { path: "/api/v1/feasibility/queue", tag: "feasibility", weight: 3, method: "GET" },
  { path: "/api/v1/feasibility/kpis", tag: "feasibility", weight: 2, method: "GET" },
  { path: "/api/v1/analytics/otd-baseline", tag: "analytics", weight: 2, method: "GET" },
  { path: "/api/v1/resolution/scenarios", tag: "resolution", weight: 1, method: "GET" },
];

const WEIGHTED_ENDPOINTS = [];
for (const ep of ENDPOINTS) {
  for (let i = 0; i < ep.weight; i++) {
    WEIGHTED_ENDPOINTS.push(ep);
  }
}

function obtainToken() {
  if (__ENV.TOKEN) {
    return __ENV.TOKEN;
  }

  if (AUTH_MODE === "keycloak") {
    const realmRes = http.get(`${KEYCLOAK_URL}/realms/ipe/.well-known/openid-configuration`);
    if (realmRes.status !== 200) {
      console.error("Keycloak discovery failed:", realmRes.status, realmRes.body);
      return "";
    }
    const tokenEndpoint = realmRes.json("token_endpoint");
    const body =
      "grant_type=password&client_id=ipe-web&username=admin@ipe.example.com&password=admin";
    const tokenRes = http.post(tokenEndpoint, body, {
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    });
    if (tokenRes.status !== 200) {
      console.error("Keycloak token grant failed:", tokenRes.status, tokenRes.body);
      return "";
    }
    return tokenRes.json("access_token") || "";
  }

  const loginRes = http.post(
    `${KONG_URL}/api/v1/auth/login`,
    JSON.stringify({ email: "Ahmed@nour", password: "admin" }),
    { headers: { "Content-Type": "application/json" } },
  );
  if (loginRes.status !== 200) {
    console.error("Local login failed:", loginRes.status, loginRes.body);
    return "";
  }
  return loginRes.json("data.access_token") || loginRes.json("access_token") || "";
}

export function setup() {
  const token = obtainToken();
  check(null, { "login successful": () => token.length > 0 });
  return { token };
}

export default function (data) {
  if (!data.token) {
    return;
  }

  const headers = {
    Authorization: `Bearer ${data.token}`,
    "X-Tenant-ID": TENANT_ID,
    "Content-Type": "application/json",
  };

  const ep = WEIGHTED_ENDPOINTS[Math.floor(Math.random() * WEIGHTED_ENDPOINTS.length)];
  const url = `${KONG_URL}${ep.path}`;

  const res =
    ep.method === "GET"
      ? http.get(url, { headers, tags: { api: ep.tag } })
      : http.post(url, "{}", { headers, tags: { api: ep.tag } });

  errorRate.add(res.status >= 400);
  apiLatency.add(res.timings.duration);

  check(res, {
    [`${ep.tag} status OK`]: (r) => r.status < 500,
  });

  // Stay under Kong 500 req/min (~8.3 req/s): 8 VU × ~1 req/1.6s ≈ 5 req/s
  sleep(Math.random() * 0.5 + 1.5);
}

function metricMs(data, key) {
  const v = data.metrics.http_req_duration?.values || {};
  if (key === "p(50)") return v.med ?? v["p(50)"];
  return v[key];
}

export function handleSummary(data) {
  const p95 = metricMs(data, "p(95)");
  const err = data.metrics.errors?.values?.rate ?? 0;
  const count = data.metrics.http_reqs?.values?.count ?? 0;
  const pass = p95 < 500 && err < 0.05;

  console.log("\n=== k6 SLO Summary (Phase 2) ===");
  console.log(`Requests: ${count}`);
  console.log(`P95: ${p95 ?? "n/a"}ms (target < 500ms)`);
  console.log(`Error rate: ${(err * 100).toFixed(2)}% (target < 5%)`);
  console.log(`SLO: ${pass ? "PASS" : "FAIL"}`);

  return {
    stdout: [
      "=== IPE k6 SLO Baseline ===",
      `requests: ${count}`,
      `p95_ms: ${p95 ?? "n/a"}`,
      `error_rate: ${(err * 100).toFixed(2)}%`,
      `slo: ${pass ? "PASS" : "FAIL"}`,
    ].join("\n"),
    "docs/qa/k6-slo-baseline.json": JSON.stringify(data, null, 2),
  };
}
