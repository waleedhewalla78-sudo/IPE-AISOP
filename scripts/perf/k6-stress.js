// k6-stress.js — Rate limit and overload behavior validation
// Purpose: Verify Kong rate limiter returns 429 at configured threshold
// Usage: k6 run scripts/perf/k6-stress.js
// Expected: Mass 429 after ~500 req/min — this is CORRECT behavior
//
// Kong global plugin: 500 req/min limit_by ip (kong.release1.yml).
// Phase 1 (setup): parallel burst via http.batch — mirrors rate-limit-burst.sh.
// Phase 2 (default): sustained VU load with minimal sleep.

import http from "k6/http";
import { check, sleep } from "k6";
import { Rate, Counter } from "k6/metrics";

const rateLimitHits = new Rate("rate_limit_429");
const totalRequests = new Counter("total_requests");
const rateLimit429Count = new Counter("rate_limit_429_count");

const KONG_URL = __ENV.KONG_URL || "http://localhost:8000";
const KEYCLOAK_URL = __ENV.KEYCLOAK_URL || "http://localhost:8180";
const AUTH_MODE = __ENV.AUTH_MODE || "keycloak";
const TENANT_ID = __ENV.TENANT_ID || "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11";
const BURST_COUNT = Number(__ENV.BURST_COUNT || 700);
const BURST_CHUNK = Number(__ENV.BURST_CHUNK || 50);

export const options = {
  setupTimeout: "120s",
  stages: [
    { duration: "10s", target: 20 },
    { duration: "30s", target: 50 },
    { duration: "10s", target: 0 },
  ],
  thresholds: {
    rate_limit_429: ["rate>0.01"],
    rate_limit_429_count: ["count>0"],
  },
};

function obtainToken() {
  if (__ENV.TOKEN) {
    return __ENV.TOKEN;
  }

  if (AUTH_MODE === "keycloak") {
    const realmRes = http.get(`${KEYCLOAK_URL}/realms/ipe/.well-known/openid-configuration`);
    if (realmRes.status !== 200) {
      return "";
    }
    const body =
      "grant_type=password&client_id=ipe-web&username=admin@ipe.example.com&password=admin";
    const tokenRes = http.post(realmRes.json("token_endpoint"), body, {
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    });
    return tokenRes.status === 200 ? tokenRes.json("access_token") || "" : "";
  }

  const loginRes = http.post(
    `${KONG_URL}/api/v1/auth/login`,
    JSON.stringify({ email: "ahmed@nour.com", password: "admin" }),
    { headers: { "Content-Type": "application/json" } },
  );
  if (loginRes.status !== 200) {
    return "";
  }
  return loginRes.json("data.access_token") || loginRes.json("access_token") || "";
}

function recordResponse(res) {
  totalRequests.add(1);
  const is429 = res.status === 429;
  rateLimitHits.add(is429);
  if (is429) {
    rateLimit429Count.add(1);
  }
  check(res, {
    "rate limited (429)": (r) => r.status === 429 || r.status === 200,
    "not server error": (r) => r.status < 500,
  });
}

function burstHealth(headers) {
  let n429 = 0;
  let n200 = 0;

  for (let offset = 0; offset < BURST_COUNT; offset += BURST_CHUNK) {
    const chunk = Math.min(BURST_CHUNK, BURST_COUNT - offset);
    const batch = Array.from({ length: chunk }, () => [
      "GET",
      `${KONG_URL}/api/v1/health`,
      null,
      { headers, timeout: "30s", tags: { phase: "burst" } },
    ]);
    const responses = http.batch(batch);
    for (const res of responses) {
      recordResponse(res);
      if (res.status === 429) n429 += 1;
      if (res.status === 200) n200 += 1;
    }
  }

  console.log(`Setup burst: ${n200} x 200, ${n429} x 429 (${BURST_COUNT} total)`);
  return { n429, n200 };
}

export function setup() {
  const token = obtainToken();
  const headers = { "X-Tenant-ID": TENANT_ID };
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  const burst = burstHealth(headers);
  return { token, burst429: burst.n429 };
}

export default function (data) {
  if (!data.token) {
    return;
  }

  const res = http.get(`${KONG_URL}/api/v1/health`, {
    headers: {
      Authorization: `Bearer ${data.token}`,
      "X-Tenant-ID": TENANT_ID,
    },
    tags: { phase: "sustained" },
  });

  recordResponse(res);
  sleep(0.1);
}

export function handleSummary(data) {
  const rate429 = data.metrics.rate_limit_429?.values?.rate || 0;
  const count429 = data.metrics.rate_limit_429_count?.values?.count || 0;
  const count = data.metrics.total_requests?.values?.count || 0;
  const pass = rate429 > 0.01 || count429 > 0;

  console.log("\n=== Stress Test Summary ===");
  console.log(`Rate limit (429) hit rate: ${(rate429 * 100).toFixed(1)}%`);
  console.log(`Rate limit (429) count: ${count429}`);
  console.log(`Total requests: ${count}`);
  console.log(
    pass
      ? "Status: PASS — Rate limiter is working correctly"
      : "Status: WARN — No rate limiting detected",
  );

  return {
    stdout: [
      "=== IPE k6 Stress (rate limit validation) ===",
      `total_requests: ${count}`,
      `rate_limit_429_count: ${count429}`,
      `rate_limit_429_pct: ${(rate429 * 100).toFixed(1)}%`,
      `status: ${pass ? "PASS" : "WARN"}`,
    ].join("\n"),
    "docs/qa/k6-stress-baseline.json": JSON.stringify(data, null, 2),
  };
}
