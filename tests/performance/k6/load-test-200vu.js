import { check, sleep } from "k6";
import http from "k6/http";
import { Rate, Trend } from "k6/metrics";

const demandFailRate = new Rate("demand_failures");
const matFailRate = new Rate("mat_failures");
const capFailRate = new Rate("cap_failures");

const demandTrend = new Trend("demand_duration");
const matTrend = new Trend("mat_duration");
const capTrend = new Trend("cap_duration");

export const options = {
  scenarios: {
    ramp_up: {
      executor: "ramping-vus",
      startVUs: 0,
      stages: [
        { duration: "30s", target: 50 },
        { duration: "2m", target: 100 },
        { duration: "2m", target: 200 },
        { duration: "3m", target: 200 },
        { duration: "30s", target: 0 },
      ],
      gracefulRampDown: "30s",
    },
  },
  thresholds: {
    checks: ["rate>0.95"],
    http_req_duration: ["p(95)<5000"],
    http_req_failed: ["rate<0.01"],
    demand_failures: ["rate<0.01"],
    mat_failures: ["rate<0.01"],
    cap_failures: ["rate<0.01"],
  },
};

const BASE_URL = __ENV.BASE_URL || "http://localhost:8000";
const TENANT_ID = __ENV.TENANT_ID || "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11";
const LOGIN_EMAIL = __ENV.LOGIN_EMAIL || "Ahmed@nour";
const LOGIN_PASSWORD = __ENV.LOGIN_PASSWORD || "admin";

const DEMAND_LINES = [
  "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a01",
  "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a02",
  "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a03",
];
const MO_IDS = [
  "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
  "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12",
];

function randomItem(arr) {
  return arr[Math.floor(Math.random() * arr.length)];
}

export function setup() {
  const loginRes = http.post(
    `${BASE_URL}/api/v1/auth/login`,
    JSON.stringify({ email: LOGIN_EMAIL, password: LOGIN_PASSWORD }),
    { headers: { "Content-Type": "application/json" }, tags: { endpoint: "auth_login" } }
  );
  check(loginRes, { "login ok": (r) => r.status === 200 && r.json("success") === true });
  const token = loginRes.json("data.access_token");
  return {
    token,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
      "X-Tenant-ID": TENANT_ID,
    },
  };
}

export default function (data) {
  const scenario = __ENV.SCENARIO || "all";
  const headers = data.headers;

  if (scenario === "all" || scenario === "demand") {
    const demandRes = http.get(`${BASE_URL}/api/v1/dashboard/demands`, {
      headers,
      tags: { endpoint: "dashboard_demands" },
    });
    demandTrend.add(demandRes.timings.duration);
    demandFailRate.add(!(demandRes.status === 200 && demandRes.json("success") === true));
    check(demandRes, {
      "demand dashboard ok": (r) => r.status === 200 && r.json("success") === true,
    });
  }

  if (scenario === "all" || scenario === "material") {
    const matRes = http.get(`${BASE_URL}/api/v1/material/inventory-summary`, {
      headers,
      tags: { endpoint: "inventory_summary" },
    });
    matTrend.add(matRes.timings.duration);
    matFailRate.add(!(matRes.status === 200));
    check(matRes, { "inventory summary ok": (r) => r.status === 200 });
  }

  if (scenario === "all" || scenario === "capacity") {
    const capRes = http.get(`${BASE_URL}/api/v1/capacity/schedule/active`, {
      headers,
      tags: { endpoint: "schedule_active" },
    });
    capTrend.add(capRes.timings.duration);
    capFailRate.add(!(capRes.status === 200 && capRes.json("success") === true));
    check(capRes, {
      "active schedule ok": (r) => r.status === 200 && r.json("success") === true,
    });
  }

  sleep(0.3);
}

export function handleSummary(data) {
  const out = __ENV.K6_SUMMARY_PATH || "specs/003-autonomous-planning-v5/evidence/r4/k6-200vu-summary.txt";
  const lines = [
    "k6 200 VU Re-certification Summary",
    `http_req_failed: ${data.metrics.http_req_failed?.values?.rate ?? "n/a"}`,
    `http_req_duration p95: ${data.metrics.http_req_duration?.values?.["p(95)"] ?? "n/a"} ms`,
    `checks pass rate: ${data.metrics.checks?.values?.rate ?? "n/a"}`,
  ];
  return {
    stdout: lines.join("\n") + "\n",
    [out]: lines.join("\n") + "\n",
  };
}
