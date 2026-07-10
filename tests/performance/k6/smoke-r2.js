/**
 * k6 smoke for Release 2 Kong surface (docker-compose.release2.yml).
 * Does NOT call mat-svc / CTP routes — those are absent from R2 compose.
 *
 * Usage:
 *   $env:BASE_URL="http://localhost:8000"
 *   k6 run tests/performance/k6/smoke-r2.js --summary-export=docs/qa/k6-smoke-r2-summary.json
 *
 * Thresholds: p95 < 5s, http_req_failed < 10%, checks > 90%
 */
import http from "k6/http";
import { check, sleep } from "k6";
import { BASE, loginSetup } from "./config.js";

export const options = {
  vus: 1,
  iterations: 5,
  thresholds: {
    http_req_duration: ["p(95)<5000"],
    http_req_failed: ["rate<0.1"],
    checks: ["rate>0.9"],
  },
};

export function setup() {
  return loginSetup();
}

function endpoints(headers) {
  return [
    {
      name: "health",
      fn: () =>
        http.get(`${BASE}/api/v1/health`, {
          headers,
          tags: { endpoint: "health" },
        }),
      ok: (r) => r.status === 200,
    },
    {
      name: "feasibility_queue",
      fn: () =>
        http.get(`${BASE}/api/v1/feasibility/queue`, {
          headers,
          tags: { endpoint: "feasibility_queue" },
        }),
      ok: (r) => r.status === 200,
    },
    {
      name: "feasibility_kpis",
      fn: () =>
        http.get(`${BASE}/api/v1/feasibility/kpis`, {
          headers,
          tags: { endpoint: "feasibility_kpis" },
        }),
      ok: (r) => r.status === 200,
    },
    {
      name: "resolution_scenarios",
      fn: () =>
        http.get(`${BASE}/api/v1/resolution/scenarios`, {
          headers,
          tags: { endpoint: "resolution_scenarios" },
        }),
      ok: (r) => r.status === 200,
    },
    {
      name: "otd_baseline",
      fn: () =>
        http.get(`${BASE}/api/v1/analytics/otd-baseline`, {
          headers,
          tags: { endpoint: "otd_baseline" },
        }),
      ok: (r) => r.status === 200,
    },
    {
      name: "sync_status",
      fn: () =>
        http.get(`${BASE}/api/v1/sync/status`, {
          headers,
          tags: { endpoint: "sync_status" },
        }),
      ok: (r) => r.status === 200,
    },
    {
      name: "demand_accuracy",
      fn: () =>
        http.get(`${BASE}/api/v1/demand/accuracy`, {
          headers,
          tags: { endpoint: "demand_accuracy" },
        }),
      ok: (r) => r.status === 200,
    },
    {
      name: "scenario_list",
      fn: () =>
        http.get(`${BASE}/api/v1/scenario`, {
          headers,
          tags: { endpoint: "scenario_list" },
        }),
      ok: (r) => r.status === 200,
    },
    {
      name: "planner_assist",
      fn: () =>
        http.post(
          `${BASE}/api/v1/planner-assist/query`,
          JSON.stringify({ query: "Which manufacturing orders are at risk?" }),
          { headers, tags: { endpoint: "planner_assist" }, timeout: "60s" },
        ),
      ok: (r) => r.status === 200,
    },
  ];
}

export default function (data) {
  for (const ep of endpoints(data.headers)) {
    const res = ep.fn();
    check(res, {
      [`${ep.name} ok`]: ep.ok,
      [`${ep.name} not 5xx`]: (r) => r.status < 500,
    });
    sleep(0.3);
  }
}
