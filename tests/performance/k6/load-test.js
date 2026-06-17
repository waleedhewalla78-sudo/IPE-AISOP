import { check } from "k6";
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
    smoke: {
      executor: "constant-vus",
      vus: 1,
      duration: "1m",
      gracefulStop: "5s",
    },
    load: {
      executor: "ramping-vus",
      startVUs: 0,
      stages: [
        { duration: "10s", target: 50 },
        { duration: "4m50s", target: 50 },
      ],
      gracefulRampDown: "10s",
    },
  },
  thresholds: {
    http_req_duration: ["p(95)<2000"],
    http_req_failed: ["rate<0.01"],
    demand_failures: ["rate<0.01"],
    mat_failures: ["rate<0.01"],
    cap_failures: ["rate<0.01"],
  },
  ext: {
    prometheusRemoteWriteURL: "http://localhost:9090/api/v1/write",
  },
};

const BASE_DEMAND = __ENV.BASE_DEMAND || "http://localhost:8001";
const BASE_MATERIAL = __ENV.BASE_MATERIAL || "http://localhost:8002";
const BASE_CAPACITY = __ENV.BASE_CAPACITY || "http://localhost:8003";

const DEMAND_LINES = [
  "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a01",
  "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a02",
  "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a03",
  "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a04",
  "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a05",
];
const MO_IDS = [
  "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
  "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12",
  "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a13",
  "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a14",
  "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a15",
];

const COMMON_HEADERS = {
  "Content-Type": "application/json",
  "X-Tenant-ID": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
};

export default function () {
  // 1. Demand classify
  const demandPayload = JSON.stringify({ demand_line_ids: DEMAND_LINES });
  const demandRes = http.post(
    `${BASE_DEMAND}/api/v1/demand/classify`,
    demandPayload,
    { headers: COMMON_HEADERS },
  );
  demandTrend.add(demandRes.timings.duration);
  demandFailRate.add(demandRes.status !== 200);
  check(demandRes, { "demand classify status 200": (r) => r.status === 200 });

  // 2. Material probabilistic ATP
  const matPayload = JSON.stringify({
    mo: { id: MO_IDS[0], product_id: "PROD-001", qty: 100 },
    components: [
      { component_id: "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a20", quantity_per: 10 },
      { component_id: "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a21", quantity_per: 5 },
    ],
    required_start: "2026-06-15T00:00:00Z",
  });
  const matRes = http.post(
    `${BASE_MATERIAL}/api/v1/material/probabilistic-atp`,
    matPayload,
    { headers: COMMON_HEADERS },
  );
  matTrend.add(matRes.timings.duration);
  matFailRate.add(matRes.status !== 200);
  check(matRes, { "mat atp status 200": (r) => r.status === 200 });

  // 3. Capacity schedule
  const capPayload = JSON.stringify({ mo_ids: MO_IDS, horizon_hours: 168 });
  const capRes = http.post(
    `${BASE_CAPACITY}/api/v1/capacity/schedule`,
    capPayload,
    { headers: COMMON_HEADERS },
  );
  capTrend.add(capRes.timings.duration);
  capFailRate.add(capRes.status !== 200);
  check(capRes, { "cap schedule status 200": (r) => r.status === 200 });
}
