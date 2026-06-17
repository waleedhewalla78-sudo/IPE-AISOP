#!/usr/bin/env python3
"""Train supplier reliability model.

Connects to CDM, queries completed supply orders (actual_date IS NOT NULL),
calculates delay days per supplier, fits a normal distribution for suppliers
with >= 10 POs, and updates cdm_supplier.delay_distribution_params and
delay_distribution_type.
"""

import argparse
import logging
import os
import statistics
import sys

from sqlalchemy import create_engine, text

logger = logging.getLogger(__name__)

MIN_PO_SAMPLE = 10


def compute_supplier_stats(rows: list[dict]) -> dict:
    delays = []
    for r in rows:
        expected = r.get("expected_date")
        actual = r.get("actual_date")
        if expected and actual:
            delay_days = (actual - expected).total_seconds() / 86400.0
            delays.append(delay_days)
    if len(delays) < MIN_PO_SAMPLE:
        return {"sample_size": len(delays), "insufficient": True}
    mu = statistics.mean(delays)
    sigma = statistics.stdev(delays) if len(delays) > 1 else 0.0
    return {
        "mu": round(mu, 4),
        "sigma": round(sigma, 4),
        "sample_size": len(delays),
        "distribution_type": "normal",
        "insufficient": False,
    }


def run_training(database_url: str, tenant_id: str | None = None, dry_run: bool = False):
    engine = create_engine(database_url.replace("+asyncpg", "+psycopg2"))
    with engine.connect() as conn:
        supplier_query = text("""
            SELECT DISTINCT s.id AS supplier_id
            FROM cdm_supplier s
            JOIN cdm_supply_order so ON so.supplier_id = s.id
            WHERE so.actual_date IS NOT NULL
        """)
        if tenant_id:
            supplier_query = text("""
                SELECT DISTINCT s.id AS supplier_id
                FROM cdm_supplier s
                JOIN cdm_supply_order so ON so.supplier_id = s.id
                WHERE so.actual_date IS NOT NULL
                  AND s.tenant_id = :tid
            """).bindparams(tid=tenant_id)

        supplier_ids = [row[0] for row in conn.execute(supplier_query).fetchall()]
        logger.info("Found %d suppliers with completed POs", len(supplier_ids))

        for sid in supplier_ids:
            po_query = text("""
                SELECT expected_date, actual_date
                FROM cdm_supply_order
                WHERE supplier_id = :sid AND actual_date IS NOT NULL
            """)
            if tenant_id:
                po_query = po_query.bindparams(sid=sid)

            rows = conn.execute(po_query, {"sid": sid}).mappings().fetchall()
            stats = compute_supplier_stats([dict(r) for r in rows])
            if stats.get("insufficient"):
                logger.info(
                    "Supplier %s: insufficient samples (%d < %d)",
                    sid, stats["sample_size"], MIN_PO_SAMPLE,
                )
                continue

            if not dry_run:
                conn.execute(
                    text("""
                        UPDATE cdm_supplier
                        SET delay_distribution_type = :dtype,
                            delay_distribution_params = :params,
                            sample_size = :sample_size,
                            avg_delay_days = :avg_delay,
                            delay_std_dev_days = :std_dev,
                            last_model_update = NOW()
                        WHERE id = :sid
                    """),
                    {
                        "dtype": "normal",
                        "params": {"mu": stats["mu"], "sigma": stats["sigma"]},
                        "sample_size": stats["sample_size"],
                        "avg_delay": stats["mu"],
                        "std_dev": stats["sigma"],
                        "sid": sid,
                    },
                )
                logger.info(
                    "Supplier %s: mu=%.4f sigma=%.4f (n=%d)",
                    sid, stats["mu"], stats["sigma"], stats["sample_size"],
                )

        if not dry_run:
            conn.commit()

    logger.info("Supplier reliability training complete.")


def main():
    parser = argparse.ArgumentParser(description="Train supplier reliability model")
    parser.add_argument("--db-url", default=os.environ.get("IPE_DATABASE_URL", ""),
                        help="Database URL (default: IPE_DATABASE_URL env)")
    parser.add_argument("--tenant-id", help="Tenant UUID (optional)")
    parser.add_argument("--dry-run", action="store_true", help="Compute stats without updating DB")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    db_url = args.db_url
    if not db_url:
        logger.error("Database URL required via --db-url or IPE_DATABASE_URL env")
        sys.exit(1)

    run_training(db_url, args.tenant_id, args.dry_run)


if __name__ == "__main__":
    main()
