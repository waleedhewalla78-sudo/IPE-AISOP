import http from "k6/http";
import { check, sleep } from "k6";
import { Rate } from "k6/metrics";
import { BASE, loginSetup, pickRandom } from "./config.js";

const serverErrorRate = new Rate("server_errors_5xx");

export const options = {
  stages: [
    { duration: "60s", target: 50 },
    { duration: "480s", target: 200 },
    { duration: "60s", target: 0 },
  ],
  thresholds: {
    http_req_duration: ["p(95)<5000", "p(99)<15000"],
    server_errors_5xx: ["rate<0.1"],
    checks: ["rate>0.8"],
  },
};

export function setup() {
  return loginSetup();
}

/** Stress mix: mostly lightweight Kong reads; avoid hammering OR-Tools at 200 VU. */
const endpoints = [
  { path: "/health", tag: "health" },
  { path: "/api/v1/feasibility/queue", tag: "feasibility_queue" },
  { path: "/api/v1/feasibility/kpis", tag: "feasibility_kpis" },
  { path: "/api/v1/material/inventory-summary", tag: "inventory_summary" },
  { path: "/api/v1/capacity/schedule/active", tag: "schedule_active" },
  { path: "/api/v1/dashboard/alerts", tag: "dashboard_alerts" },
  { path: "/api/v1/analytics/executive-summary", tag: "executive_summary" },
];

export default function (data) {
  const ep = pickRandom(endpoints);
  const res = http.get(`${BASE}${ep.path}`, {
    headers: data.headers,
    tags: { endpoint: ep.tag },
  });
  check(res, {
    [`${ep.tag} not 5xx`]: (r) => r.status < 500,
    [`${ep.tag} 200`]: (r) => r.status === 200,
  });
  serverErrorRate.add(res.status >= 500);
  sleep(0.1 + Math.random() * 0.3);
}
