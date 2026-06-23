"""Register Avro schemas with the Confluent Schema Registry.

Sets BACKWARD compatibility on each subject.
Idempotent: re-running does not error if the subject already exists.

Usage:
    uv run python scripts/register_schemas.py
"""
import json
import sys
from pathlib import Path

import httpx

SCHEMA_REGISTRY_URL = "http://localhost:8083"
SCHEMA_DIR = Path(__file__).resolve().parent.parent / "services" / "shared" / "ipe_shared" / "events" / "schemas"

TOPICS = [
    "ipe.demand.created",
    "ipe.demand.classified",
    "ipe.mo.material_scored",
    "ipe.supply.delay_detected",
    "ipe.mo.feasibility_scored",
    "ipe.mo.capacity_scored",
    "ipe.resolution.proposed",
    "ipe.resolution.approved",
    "ipe.delay.logged",
    "ipe.disruption.detected",
    "ipe.schedule.updated",
    "ipe.ml.duration.predicted",
]


def set_compatibility(subject: str, compat: str = "BACKWARD") -> bool:
    url = f"{SCHEMA_REGISTRY_URL}/config/{subject}"
    try:
        resp = httpx.put(url, json={"compatibility": compat}, timeout=10)
        if resp.status_code in (200, 201):
            return True
        if resp.status_code == 422 and "is already at level" in resp.text:
            return True
        print(f"  WARN: compat for {subject}: {resp.status_code} {resp.text}")
        return False
    except Exception as e:
        print(f"  WARN: cannot set compat for {subject}: {e}")
        return False


def main():
    if not SCHEMA_DIR.is_dir():
        print(f"Schema directory not found: {SCHEMA_DIR}")
        sys.exit(1)

    for topic in TOPICS:
        schema_name = topic.replace(".", "_")
        schema_file = SCHEMA_DIR / f"{schema_name}.avsc"
        if not schema_file.exists():
            print(f"  SKIP {topic}: schema file {schema_file.name} not found")
            continue

        with open(schema_file) as f:
            schema = json.load(f)

        subject = f"{topic}-value"
        url = f"{SCHEMA_REGISTRY_URL}/subjects/{subject}/versions"
        print(f"  Registering {subject}...", end=" ")

        try:
            resp = httpx.post(url, json={"schema": json.dumps(schema)}, timeout=10)
            if resp.status_code in (200, 201):
                print(f"OK (id={resp.json().get('id', '?')})")
            elif resp.status_code == 409:
                print("OK (already exists)")
            else:
                print(f"FAILED ({resp.status_code}): {resp.text}")
                continue
        except httpx.ConnectError:
            print(f"FAILED (cannot connect to Schema Registry at {SCHEMA_REGISTRY_URL})")
            continue

        set_compatibility(subject, "BACKWARD")

    print("\nAll schemas registered with BACKWARD compatibility.")


if __name__ == "__main__":
    main()
