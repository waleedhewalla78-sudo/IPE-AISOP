#!/usr/bin/env python3
"""Train cycle time prediction model.

Connects to CDM, queries completed work orders (status = 'completed'),
calculates the ratio of duration_actual_mins to duration_planned_mins
per (product_id, work_center_id), and updates
cdm_routing_operation.duration_predicted_mins with the actual average where
the product's BOM routing contains that operation.
"""

import argparse
import logging
import os
import sys

from sqlalchemy import create_engine, text

logger = logging.getLogger(__name__)


def run_training(database_url: str, tenant_id: str | None = None, dry_run: bool = False):
    engine = create_engine(database_url.replace("+asyncpg", "+psycopg2"))
    with engine.connect() as conn:
        ratio_query = text("""
            SELECT
                wo.routing_op_id,
                wo.work_center_id,
                mo.product_id,
                AVG(wo.duration_actual_mins / NULLIF(wo.duration_planned_mins, 0)) AS avg_ratio,
                AVG(wo.duration_actual_mins) AS avg_actual_mins,
                COUNT(*) AS sample_count
            FROM cdm_work_order wo
            JOIN cdm_manufacturing_order mo ON mo.id = wo.mo_id
            WHERE wo.status = 'completed'
              AND wo.duration_actual_mins IS NOT NULL
              AND wo.duration_planned_mins IS NOT NULL
              AND wo.duration_planned_mins > 0
        """)
        if tenant_id:
            ratio_query = text("""
                SELECT
                    wo.routing_op_id,
                    wo.work_center_id,
                    mo.product_id,
                    AVG(wo.duration_actual_mins / NULLIF(wo.duration_planned_mins, 0)) AS avg_ratio,
                    AVG(wo.duration_actual_mins) AS avg_actual_mins,
                    COUNT(*) AS sample_count
                FROM cdm_work_order wo
                JOIN cdm_manufacturing_order mo ON mo.id = wo.mo_id
                WHERE wo.status = 'completed'
                  AND wo.duration_actual_mins IS NOT NULL
                  AND wo.duration_planned_mins IS NOT NULL
                  AND wo.duration_planned_mins > 0
                  AND wo.tenant_id = :tid
                GROUP BY wo.routing_op_id, wo.work_center_id, mo.product_id
            """).bindparams(tid=tenant_id)
        else:
            ratio_query = ratio_query.bindparams()

        rows = conn.execute(ratio_query).fetchall()
        logger.info("Found %d product-work_center combinations", len(rows))

        updated = 0
        for row in rows:
            routing_op_id = row[0]
            avg_actual_mins = row[3]
            if avg_actual_mins is None:
                continue

            predicted = round(float(avg_actual_mins), 2)

            if not dry_run:
                conn.execute(
                    text("""
                        UPDATE cdm_routing_operation
                        SET duration_predicted_mins = :predicted,
                            prediction_confidence = :confidence
                        WHERE id = :rid
                    """),
                    {
                        "predicted": predicted,
                        "confidence": 0.85,
                        "rid": routing_op_id,
                    },
                )
                updated += 1

        if not dry_run:
            conn.commit()

        logger.info("Updated %d routing operations with predicted durations.", updated)


def main():
    parser = argparse.ArgumentParser(description="Train cycle time prediction model")
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
