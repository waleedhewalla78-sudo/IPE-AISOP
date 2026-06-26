import http from "k6/http";
import { check } from "k6";

export const BASE = __ENV.BASE_URL || "http://localhost:8000";
export const TENANT_ID = __ENV.TENANT_ID || "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11";
export const LOGIN_EMAIL = __ENV.LOGIN_EMAIL || "Ahmed@nour";
export const LOGIN_PASSWORD = __ENV.LOGIN_PASSWORD || "admin";

/** Demo MO subset (matches scripts/run-full-demo.ps1). */
export const DEMO_MO_IDS = [
  "d1eebc99-9c0b-4ef8-bb6d-6bb9bd380001",
  "d1eebc99-9c0b-4ef8-bb6d-6bb9bd380002",
  "d1eebc99-9c0b-4ef8-bb6d-6bb9bd380003",
];

/** Widget A product UUID from seed-demo-client.sql */
export const WIDGET_A_PRODUCT_ID = "e1eebc99-9c0b-4ef8-bb6d-6bb9bd380a01";

export function loginSetup() {
  const loginRes = http.post(
    `${BASE}/api/v1/auth/login`,
    JSON.stringify({ email: LOGIN_EMAIL, password: LOGIN_PASSWORD }),
    { headers: { "Content-Type": "application/json" }, tags: { endpoint: "auth_login" } },
  );
  check(loginRes, {
    "login status 200": (r) => r.status === 200,
    "login success": (r) => r.json("success") === true,
  });
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

export function pickRandom(arr) {
  return arr[Math.floor(Math.random() * arr.length)];
}
