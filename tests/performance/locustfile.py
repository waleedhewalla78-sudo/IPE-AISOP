"""
Locust performance test for IPE microservices.

Simulates 50 concurrent users for 2 minutes, targeting:
  - DemandUser: POST /api/v1/demand/classify (50 demand lines)
  - CapacityUser: POST /api/v1/capacity/schedule (20 MOs)

Slap target:
  95th percentile response time < 2000ms
"""

from uuid import uuid4

from locust import HttpUser, between, task

DEMAND_LINES = [str(uuid4()) for _ in range(50)]
MO_IDS = [str(uuid4()) for _ in range(20)]

COMMON_HEADERS = {
    "Content-Type": "application/json",
    "X-Tenant-ID": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
    "Authorization": "Bearer ipe-service-key",
}


class DemandUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def classify_demand(self):
        payload = {"demand_line_ids": DEMAND_LINES}
        with self.client.post(
            "/api/v1/demand/classify",
            json=payload,
            headers=COMMON_HEADERS,
            catch_response=True,
            name="POST /demand/classify (50 lines)",
        ) as resp:
            if resp.elapsed.total_seconds() * 1000 > 2000:
                resp.failure(f"Response time exceeded 2000ms: {resp.elapsed.total_seconds() * 1000:.0f}ms")
            elif resp.status_code != 200:
                resp.failure(f"HTTP {resp.status_code}")


class CapacityUser(HttpUser):
    wait_time = between(2, 5)

    @task
    def schedule_capacity(self):
        payload = {"mo_ids": MO_IDS, "horizon_hours": 168}
        with self.client.post(
            "/api/v1/capacity/schedule",
            json=payload,
            headers=COMMON_HEADERS,
            catch_response=True,
            name="POST /capacity/schedule (20 MOs)",
        ) as resp:
            if resp.elapsed.total_seconds() * 1000 > 2000:
                resp.failure(f"Response time exceeded 2000ms: {resp.elapsed.total_seconds() * 1000:.0f}ms")
            elif resp.status_code != 200:
                resp.failure(f"HTTP {resp.status_code}")
