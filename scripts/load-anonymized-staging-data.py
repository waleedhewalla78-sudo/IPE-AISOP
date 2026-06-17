#!/usr/bin/env python3
"""
load-anonymized-staging-data.py

Connects to a production-like database, anonymizes PII, and loads a
representative dataset (1000 MOs, 500 supply orders) into a staging
environment for User Acceptance Testing (UAT).

Usage:
    python scripts/load-anonymized-staging-data.py \
        --source-dsn postgresql://... \
        --target-dsn postgresql://... \
        --tenant-id <UUID> \
        --mos 1000 \
        --supply-orders 500
"""

import argparse
import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from random import gauss, randint, seed as random_seed

random_seed(42)


def _anonymize(value: str | None, salt: str = "ipe-anon") -> str | None:
    """Replace a PII string with its SHA-256 hex digest (truncated to 32 chars)."""
    if value is None:
        return None
    raw = f"{value}:::{salt}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


def _generate_mos(
    count: int, tenant_id: str
) -> list[dict]:
    """Generate realistic MOs with anonymized planner references."""
    mos: list[dict] = []
    statuses = ["planned", "released", "completed", "canceled"]
    priorities = ["urgent", "high", "normal", "low"]
    now = datetime.now(timezone.utc)

    for i in range(count):
        priority = priorities[randint(0, 3)]
        priority_score = {"urgent": 0.95, "high": 0.75, "normal": 0.50, "low": 0.25}[priority]
        planned_duration = max(60, int(gauss(480, 120)))  # minutes, mean 8h
        created_at = now - timedelta(days=randint(1, 90))
        planned_start = created_at + timedelta(hours=randint(8, 72))
        actual_start = planned_start if statuses[randint(0, 3)] == "completed" else None
        actual_end = actual_start + timedelta(minutes=planned_duration) if actual_start else None

        mos.append(
            {
                "id": str(uuid.uuid4()),
                "tenant_id": tenant_id,
                "bom_id": f"BOM-{randint(1000, 9999)}",
                "product_code": f"SKU-{randint(10000, 99999)}",
                "quantity": max(1, int(gauss(100, 30))),
                "status": statuses[randint(0, 3)],
                "priority": priority,
                "priority_score": priority_score,
                "planned_duration_minutes": planned_duration,
                "actual_duration_minutes": planned_duration + int(gauss(0, 30)) if actual_start else None,
                "due_date": (planned_start + timedelta(hours=randint(24, 168))).isoformat(),
                "planned_start": planned_start.isoformat(),
                "actual_start": actual_start.isoformat() if actual_start else None,
                "actual_end": actual_end.isoformat() if actual_end else None,
                "assigned_planner": _anonymize(f"planner-{randint(1, 20)}@example.com"),
                "created_at": created_at.isoformat(),
                "updated_at": now.isoformat(),
            }
        )
    return mos


def _generate_supply_orders(
    count: int, tenant_id: str
) -> list[dict]:
    """Generate realistic supply orders with anonymized supplier names."""
    orders: list[dict] = []
    now = datetime.now(timezone.utc)

    for i in range(count):
        lead_time_days = max(1, int(gauss(14, 5)))
        planned_delivery = now + timedelta(days=lead_time_days)
        actual_delivery = planned_delivery + timedelta(days=int(gauss(0, 3)))

        orders.append(
            {
                "id": str(uuid.uuid4()),
                "tenant_id": tenant_id,
                "mo_id": None,  # linked at load time
                "supplier_name": _anonymize(f"supplier-{randint(1, 50)}"),
                "supplier_id": f"SUP-{randint(1000, 9999)}",
                "material_code": f"MAT-{randint(10000, 99999)}",
                "quantity": max(1, int(gauss(500, 150))),
                "order_date": (now - timedelta(days=randint(1, 60))).isoformat(),
                "planned_delivery_date": planned_delivery.isoformat(),
                "actual_delivery_date": actual_delivery.isoformat(),
                "planned_lead_days": lead_time_days,
                "actual_lead_days": lead_time_days + int(gauss(0, 3)),
                "status": "delivered" if randint(0, 2) > 0 else "pending",
                "created_at": (now - timedelta(days=randint(1, 60))).isoformat(),
            }
        )
    return orders


def _create_tables(target_dsn: str) -> None:
    """Create staging tables if they do not exist."""
    import psycopg2

    conn = psycopg2.connect(target_dsn)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS staging_manufacturing_order (
            id UUID PRIMARY KEY,
            tenant_id UUID NOT NULL,
            bom_id VARCHAR(50),
            product_code VARCHAR(50),
            quantity INTEGER,
            status VARCHAR(20),
            priority VARCHAR(20),
            priority_score REAL,
            planned_duration_minutes INTEGER,
            actual_duration_minutes INTEGER,
            due_date TIMESTAMPTZ,
            planned_start TIMESTAMPTZ,
            actual_start TIMESTAMPTZ,
            actual_end TIMESTAMPTZ,
            assigned_planner VARCHAR(64),
            created_at TIMESTAMPTZ,
            updated_at TIMESTAMPTZ
        );

        CREATE TABLE IF NOT EXISTS staging_supply_order (
            id UUID PRIMARY KEY,
            tenant_id UUID NOT NULL,
            mo_id UUID,
            supplier_name VARCHAR(64),
            supplier_id VARCHAR(20),
            material_code VARCHAR(20),
            quantity INTEGER,
            order_date TIMESTAMPTZ,
            planned_delivery_date TIMESTAMPTZ,
            actual_delivery_date TIMESTAMPTZ,
            planned_lead_days INTEGER,
            actual_lead_days INTEGER,
            status VARCHAR(20),
            created_at TIMESTAMPTZ
        );
        """
    )
    conn.commit()
    cur.close()
    conn.close()


def _truncate_staging(target_dsn: str) -> None:
    """Remove existing staging data."""
    import psycopg2

    conn = psycopg2.connect(target_dsn)
    cur = conn.cursor()
    cur.execute("TRUNCATE staging_manufacturing_order, staging_supply_order;")
    conn.commit()
    cur.close()
    conn.close()


def load_data(
    target_dsn: str,
    mos: list[dict],
    supply_orders: list[dict],
) -> dict:
    """Bulk-insert generated data into the staging tables."""
    import psycopg2
    from psycopg2.extras import execute_values

    conn = psycopg2.connect(target_dsn)
    cur = conn.cursor()

    insert_mos = """
        INSERT INTO staging_manufacturing_order (
            id, tenant_id, bom_id, product_code, quantity, status,
            priority, priority_score, planned_duration_minutes,
            actual_duration_minutes, due_date, planned_start,
            actual_start, actual_end, assigned_planner,
            created_at, updated_at
        ) VALUES %s
    """
    mo_rows = [
        (
            m["id"], m["tenant_id"], m["bom_id"], m["product_code"],
            m["quantity"], m["status"], m["priority"], m["priority_score"],
            m["planned_duration_minutes"], m["actual_duration_minutes"],
            m["due_date"], m["planned_start"], m["actual_start"],
            m["actual_end"], m["assigned_planner"],
            m["created_at"], m["updated_at"],
        )
        for m in mos
    ]
    execute_values(cur, insert_mos, mo_rows)

    insert_orders = """
        INSERT INTO staging_supply_order (
            id, tenant_id, mo_id, supplier_name, supplier_id,
            material_code, quantity, order_date,
            planned_delivery_date, actual_delivery_date,
            planned_lead_days, actual_lead_days, status, created_at
        ) VALUES %s
    """
    order_rows = [
        (
            o["id"], o["tenant_id"], o["mo_id"], o["supplier_name"],
            o["supplier_id"], o["material_code"], o["quantity"],
            o["order_date"], o["planned_delivery_date"],
            o["actual_delivery_date"], o["planned_lead_days"],
            o["actual_lead_days"], o["status"], o["created_at"],
        )
        for o in supply_orders
    ]
    execute_values(cur, insert_orders, order_rows)

    conn.commit()
    cur.close()
    conn.close()

    return {
        "mos_inserted": len(mos),
        "supply_orders_inserted": len(supply_orders),
        "status": "success",
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Load anonymized staging data for UAT"
    )
    parser.add_argument("--target-dsn", required=True, help="Target database DSN")
    parser.add_argument("--tenant-id", required=True, help="Tenant UUID")
    parser.add_argument("--mos", type=int, default=1000, help="Number of MOs (default: 1000)")
    parser.add_argument(
        "--supply-orders", type=int, default=500, help="Number of supply orders (default: 500)"
    )
    args = parser.parse_args()

    print(f"Generating {args.mos} MOs and {args.supply_orders} supply orders...")
    mos = _generate_mos(args.mos, args.tenant_id)
    supply_orders = _generate_supply_orders(args.supply_orders, args.tenant_id)
    print("Data generation complete.")

    print("Creating staging tables...")
    _create_tables(args.target_dsn)

    print("Truncating existing staging data...")
    _truncate_staging(args.target_dsn)

    print("Loading data...")
    result = load_data(args.target_dsn, mos, supply_orders)
    print(f"Loaded {result['mos_inserted']} MOs and {result['supply_orders_inserted']} supply orders.")
    print("Done.")


if __name__ == "__main__":
    main()
