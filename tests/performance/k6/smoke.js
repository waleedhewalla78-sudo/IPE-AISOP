import http from "k6/http";
import { check, sleep } from "k6";
import {
  BASE,
  DEMO_MO_IDS,
  WIDGET_A_PRODUCT_ID,
  loginSetup,
} from "./config.js";

export const options = {
  vus: 1,
  iterations: 10,
  thresholds: {
    http_req_duration: ["p(95)<30000"],
    http_req_failed: ["rate<0.2"],
    checks: ["rate>0.85"],
  },
};

export function setup() {
  return loginSetup();
}

/**
 * Full-stack smoke (mat/CTP/capacity). For R2 compose use smoke-r2.js instead.
 * Set PROFILE=r2 to skip mat-svc / CTP routes not present on Kong R2.
 */
const PROFILE = (__ENV.PROFILE || "full").toLowerCase();

const endpoints = (headers) => {
  const common = [
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
  ];

  if (PROFILE === "r2") {
    return [
      ...common,
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
    ];
  }

  return [
    ...common,
    {
      name: "inventory_summary",
      fn: () =>
        http.get(`${BASE}/api/v1/material/inventory-summary`, {
          headers,
          tags: { endpoint: "inventory_summary" },
        }),
      ok: (r) => r.status === 200,
    },
    {
      name: "schedule_active",
      fn: () =>
        http.get(`${BASE}/api/v1/capacity/schedule/active`, {
          headers,
          tags: { endpoint: "schedule_active" },
        }),
      ok: (r) => r.status === 200 && r.json("success") === true,
    },
    {
      name: "check_availability",
      fn: () =>
        http.post(
          `${BASE}/api/v1/material/check-availability`,
          JSON.stringify({
            product_id: WIDGET_A_PRODUCT_ID,
            quantity: 10,
            required_date: "2026-07-01T00:00:00Z",
          }),
          { headers, tags: { endpoint: "check_availability" } },
        ),
      ok: (r) => r.status === 200 && r.json("success") === true,
    },
    {
      name: "ctp_evaluate",
      fn: () =>
        http.post(
          `${BASE}/api/v1/ctp/evaluate`,
          JSON.stringify({
            so_id: 1001,
            product_id: 1001,
            requested_qty: 10,
            requested_delivery_date: "2026-07-15T00:00:00Z",
            customer_priority: "medium",
          }),
          { headers, tags: { endpoint: "ctp_evaluate" } },
        ),
      ok: (r) => r.status === 200,
    },
    {
      name: "capacity_schedule",
      fn: () =>
        http.post(
          `${BASE}/api/v1/capacity/schedule`,
          JSON.stringify({ mo_ids: DEMO_MO_IDS }),
          { headers, timeout: "90s", tags: { endpoint: "capacity_schedule" } },
        ),
      ok: (r) => r.status === 200 && r.json("success") === true,
    },
  ];
};

export default function (data) {
  for (const ep of endpoints(data.headers)) {
    const res = ep.fn();
    check(res, {
      [`${ep.name} ok`]: ep.ok,
      [`${ep.name} not 5xx`]: (r) => r.status < 500,
    });
    sleep(0.5);
  }
}
