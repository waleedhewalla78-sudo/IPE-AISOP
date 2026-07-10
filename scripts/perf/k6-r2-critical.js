// k6-r2-critical.js — R2 critical API cycle against live Kong
// Covers: health, auth, demand, scenario, planning/feasibility, OTD
// Usage: AUTH_MODE=local k6 run scripts/perf/k6-r2-critical.js

import http from "k6/http";
import { check, group, sleep } from "k6";
import { Rate, Trend } from "k6/metrics";

const errorRate = new Rate("errors");
const apiLatency = new Trend("api_latency");

const KONG_URL = __ENV.KONG_URL || __ENV.BASE_URL || "http://localhost:8000";
const AUTH_MODE = __ENV.AUTH_MODE || "local";
const TENANT_ID = __ENV.TENANT_ID || "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11";
const KEYCLOAK_URL = __ENV.KEYCLOAK_URL || "http://localhost:8180";

export const options = {
  scenarios: {
    critical_cycle: {
      executor: "constant-vus",
      vus: 3,
      duration: "90s",
    },
  },
  thresholds: {
    // Allow brief Kong/upstream warm-up noise; hard fail on sustained auth/5xx.
    errors: ["rate<0.10"],
    api_latency: ["p(95)<2000"],
    checks: ["rate>0.85"],
    "http_req_duration{api:health}": ["p(95)<2000"],
    "http_req_duration{api:demand}": ["p(95)<2000"],
    "http_req_duration{api:scenario}": ["p(95)<2000"],
  },
};

function obtainToken() {
  if (__ENV.TOKEN) return __ENV.TOKEN;

  if (AUTH_MODE === "keycloak") {
    const realmRes = http.get(`${KEYCLOAK_URL}/realms/ipe/.well-known/openid-configuration`);
    if (realmRes.status !== 200) return "";
    const tokenEndpoint = realmRes.json("token_endpoint");
    const body =
      "grant_type=password&client_id=ipe-web&username=admin@ipe.example.com&password=admin";
    const tokenRes = http.post(tokenEndpoint, body, {
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    });
    if (tokenRes.status !== 200) return "";
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

function hit(name, method, path, token, body) {
  const headers = {
    Authorization: `Bearer ${token}`,
    "X-Tenant-ID": TENANT_ID,
    "Content-Type": "application/json",
  };
  const url = `${KONG_URL}${path}`;
  const res =
    method === "GET"
      ? http.get(url, { headers, tags: { api: name } })
      : http.post(url, body || "{}", { headers, tags: { api: name } });
  errorRate.add(res.status >= 400);
  apiLatency.add(res.timings.duration);
  check(res, {
    [`${name} not 5xx`]: (r) => r.status < 500,
    [`${name} auth ok`]: (r) => r.status !== 401 && r.status !== 403,
  });
  return res;
}

export default function (data) {
  if (!data.token) return;

  group("health", () => {
    hit("health", "GET", "/api/v1/health", data.token);
  });

  group("planning", () => {
    hit("feasibility", "GET", "/api/v1/feasibility/queue", data.token);
    hit("feasibility", "GET", "/api/v1/feasibility/kpis", data.token);
    hit("analytics", "GET", "/api/v1/analytics/otd-baseline", data.token);
  });

  group("demand", () => {
    hit("demand", "GET", "/api/v1/demand/accuracy", data.token);
  });

  group("scenario", () => {
    hit("scenario", "GET", "/api/v1/scenario", data.token);
  });

  sleep(2.5 + Math.random()); // Keep under Kong ~500 req/min with 3 VUs × 6 GETs
}

export function handleSummary(data) {
  const p95 = data.metrics.api_latency?.values?.["p(95)"];
  const err = data.metrics.errors?.values?.rate ?? 0;
  const count = data.metrics.http_reqs?.values?.count ?? 0;
  const checks = data.metrics.checks?.values?.rate ?? 0;
  const pass = err < 0.1 && checks > 0.85;

  console.log("\n=== k6 R2 Critical Summary ===");
  console.log(`Requests: ${count}`);
  console.log(`P95 latency: ${p95 ?? "n/a"}ms`);
  console.log(`Error rate: ${(err * 100).toFixed(2)}%`);
  console.log(`Checks: ${(checks * 100).toFixed(2)}%`);
  console.log(`Result: ${pass ? "PASS" : "FAIL"}`);

  return {
    stdout: [
      "=== IPE k6 R2 Critical ===",
      `requests: ${count}`,
      `p95_ms: ${p95 ?? "n/a"}`,
      `error_rate: ${(err * 100).toFixed(2)}%`,
      `checks: ${(checks * 100).toFixed(2)}%`,
      `result: ${pass ? "PASS" : "FAIL"}`,
    ].join("\n"),
    "docs/qa/k6-r2-critical-summary.json": JSON.stringify(
      {
        requests: count,
        p95_ms: p95,
        error_rate: err,
        checks,
        result: pass ? "PASS" : "FAIL",
        metrics: data.metrics,
      },
      null,
      2,
    ),
  };
}
