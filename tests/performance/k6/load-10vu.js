import http from "k6/http";
import { check, sleep } from "k6";
import { Rate } from "k6/metrics";
import {
  BASE,
  DEMO_MO_IDS,
  WIDGET_A_PRODUCT_ID,
  loginSetup,
  pickRandom,
} from "./config.js";

const serverErrorRate = new Rate("server_errors_5xx");

export const options = {
  stages: [
    { duration: "30s", target: 5 },
    { duration: "240s", target: 10 },
    { duration: "30s", target: 0 },
  ],
  thresholds: {
    http_req_duration: ["p(95)<10000", "p(99)<30000"],
    server_errors_5xx: ["rate<0.05"],
    checks: ["rate>0.9"],
  },
};

export function setup() {
  return loginSetup();
}

const readEndpoints = (headers) => [
  {
    path: "/api/v1/feasibility/queue",
    method: "GET",
    body: null,
    tag: "feasibility_queue",
  },
  {
    path: "/api/v1/material/inventory-summary",
    method: "GET",
    body: null,
    tag: "inventory_summary",
  },
  {
    path: "/api/v1/capacity/schedule/active",
    method: "GET",
    body: null,
    tag: "schedule_active",
  },
  {
    path: "/health",
    method: "GET",
    body: null,
    tag: "health",
  },
];

const writeEndpoints = (headers) => [
  {
    path: "/api/v1/material/check-availability",
    body: {
      product_id: WIDGET_A_PRODUCT_ID,
      quantity: 50,
      required_date: "2026-07-01T00:00:00Z",
    },
    tag: "check_availability",
  },
  {
    path: "/api/v1/ctp/evaluate",
    body: {
      so_id: 1001,
      product_id: 1001,
      requested_qty: 10,
      requested_delivery_date: "2026-07-15T00:00:00Z",
      customer_priority: "medium",
    },
    tag: "ctp_evaluate",
  },
];

export default function (data) {
  const headers = data.headers;
  // 80% read-heavy, 20% writes (schedule solver is expensive)
  const roll = Math.random();
  let res;
  if (roll < 0.55) {
    const ep = pickRandom(readEndpoints());
    res = http.get(`${BASE}${ep.path}`, { headers, tags: { endpoint: ep.tag } });
  } else if (roll < 0.85) {
    const ep = pickRandom(writeEndpoints());
    res = http.post(`${BASE}${ep.path}`, JSON.stringify(ep.body), {
      headers,
      tags: { endpoint: ep.tag },
    });
  } else {
    res = http.post(
      `${BASE}/api/v1/capacity/schedule`,
      JSON.stringify({ mo_ids: DEMO_MO_IDS }),
      { headers, timeout: "90s", tags: { endpoint: "capacity_schedule" } },
    );
  }
  check(res, {
    "status not 5xx": (r) => r.status < 500,
  });
  serverErrorRate.add(res.status >= 500);
  sleep(0.3 + Math.random() * 0.7);
}
