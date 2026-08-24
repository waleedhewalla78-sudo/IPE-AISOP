"""Seed Sprint 2 development data."""
import asyncio
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ipe_shared.database.connection import get_engine, init_database
from ipe_shared.config import settings


async def seed():
    await init_database(settings.DATABASE_URL)
    engine = get_engine()
    factory = async_sessionmaker(engine, expire_on_commit=False)

    async with factory() as session:
        tenant_id = uuid.uuid4()

        result = await session.execute(
            text("SELECT id FROM cdm_tenant WHERE name = :name"), {"name": "demo_tenant"}
        )
        existing = result.fetchone()
        if existing:
            tenant_id = existing[0]
            print(f"Tenant already exists: {tenant_id}")
        else:
            await session.execute(
                text("""
                    INSERT INTO cdm_tenant (id, name, tier, erp_type, autonomy_mode, config)
                    VALUES (:id, 'demo_tenant', 'premium', 'odoo', 'shadow', '{}')
                """),
                {"id": tenant_id},
            )
            print(f"Created tenant: {tenant_id}")

        user_id = uuid.uuid4()
        await session.execute(
            text("""
                INSERT INTO cdm_user (id, tenant_id, email, role)
                VALUES (:id, :tid, 'planner@demo.com', 'planner')
                ON CONFLICT (tenant_id, email) DO NOTHING
            """),
            {"id": user_id, "tid": tenant_id},
        )

        product_names = [
            "Distribution Transformer 500 kVA",
            "Pad-Mount Transformer 250 kVA",
            "Copper Winding Wire",
            "Power Transformer 50 MVA Core-Coil",
            "CRGO Electrical Steel",
        ]
        product_ids = []
        for idx, name in enumerate(product_names, start=1):
            pid = uuid.uuid4()
            await session.execute(
                text("""
                    INSERT INTO cdm_product (id, tenant_id, erp_source_id, name, source_type, lead_time_days)
                    VALUES (:id, :tid, :eid, :name, 'manufactured', 5.0)
                    ON CONFLICT (tenant_id, erp_source_id) DO UPDATE SET name = EXCLUDED.name
                """),
                {"id": pid, "tid": tenant_id, "eid": f"PROD{idx:03d}", "name": name},
            )
            product_ids.append(pid)

        bom_id = uuid.uuid4()
        await session.execute(
            text("""
                INSERT INTO cdm_bill_of_material (id, tenant_id, product_id, erp_source_id, is_active)
                VALUES (:id, :tid, :pid, 'BOM-001', true)
                ON CONFLICT DO NOTHING
            """),
            {"id": bom_id, "tid": tenant_id, "pid": product_ids[0]},
        )

        for i, comp_id in enumerate(product_ids[1:], 1):
            await session.execute(
                text("""
                    INSERT INTO cdm_bom_line (id, tenant_id, bom_id, component_id, quantity_per, is_critical)
                    VALUES (:id, :tid, :bom_id, :comp_id, :qty, :crit)
                    ON CONFLICT DO NOTHING
                """),
                {"id": uuid.uuid4(), "tid": tenant_id, "bom_id": bom_id,
                 "comp_id": comp_id, "qty": 2.0 * i, "crit": i == 1},
            )

        wc_ids = []
        for name in ["CNC Machine", "Assembly Line", "Paint Station"]:
            wc_id = uuid.uuid4()
            await session.execute(
                text("""
                    INSERT INTO cdm_work_center (id, tenant_id, erp_source_id, name, capacity_hours_per_day)
                    VALUES (:id, :tid, :eid, :name, 16.0)
                    ON CONFLICT DO NOTHING
                """),
                {"id": wc_id, "tid": tenant_id, "eid": f"WC-{name[:3]}", "name": name},
            )
            wc_ids.append(wc_id)

        supplier_ids = []
        for name, delay_type, sample_size in [
            ("Reliable Supply Co", "normal", 50),
            ("Variable Parts Inc", "lognormal", 15),
            ("Premium Materials Ltd", "normal", 100),
        ]:
            sid = uuid.uuid4()
            await session.execute(
                text("""
                    INSERT INTO cdm_supplier (id, tenant_id, erp_source_id, name, reliability_score,
                                             avg_delay_days, delay_std_dev_days, delay_distribution_type, sample_size)
                    VALUES (:id, :tid, :eid, :name, :rel, :avg_delay, :std_dev, :dist_type, :sample)
                    ON CONFLICT DO NOTHING
                """),
                {"id": sid, "tid": tenant_id, "eid": f"SUPP-{name[:4]}", "name": name,
                 "rel": 0.85 if sample_size >= 30 else 0.6,
                 "avg_delay": 2.0 if sample_size >= 30 else 5.0,
                 "std_dev": 1.0 if sample_size >= 30 else 3.0,
                 "dist_type": delay_type, "sample": sample_size},
            )
            supplier_ids.append(sid)

        for i in range(10):
            dl_id = uuid.uuid4()
            mo_id = uuid.uuid4()
            days_ahead = (i % 20) + 5
            await session.execute(
                text("""
                    INSERT INTO cdm_manufacturing_order (id, tenant_id, product_id, bom_id, quantity,
                                                         planned_start, planned_end, status,
                                                         material_score, feasibility_score)
                    VALUES (:id, :tid, :pid, :bom_id, :qty, :start, :end, :status, :mat_score, :feas_score)
                    ON CONFLICT DO NOTHING
                """),
                {"id": mo_id, "tid": tenant_id, "pid": product_ids[i % len(product_ids)],
                 "bom_id": bom_id, "qty": 100 + i * 10,
                 "start": datetime.now(UTC) + timedelta(days=days_ahead),
                 "end": datetime.now(UTC) + timedelta(days=days_ahead + 3),
                 "status": "draft" if i < 5 else "planned",
                 "mat_score": 65.0 + i * 3 if i < 5 else None,
                 "feas_score": None},
            )

            await session.execute(
                text("""
                    INSERT INTO cdm_demand_line (id, tenant_id, erp_source_id, product_id, quantity,
                                                 required_date, demand_type, priority_score, mo_id, status)
                    VALUES (:id, :tid, :eid, :pid, :qty, :req_date, :dtype, :pscore, :mo_id, :status)
                    ON CONFLICT DO NOTHING
                """),
                {"id": dl_id, "tid": tenant_id, "eid": f"DL-{i+1:04d}",
                 "pid": product_ids[i % len(product_ids)], "qty": 100 + i * 10,
                 "req_date": datetime.now(UTC) + timedelta(days=days_ahead),
                 "dtype": "MTO" if i < 3 else "MTS" if i < 7 else "CTO",
                 "pscore": 0.9 - (i * 0.05), "mo_id": mo_id,
                 "status": "new" if i < 8 else "classified"},
            )

        for i in range(5):
            await session.execute(
                text("""
                    INSERT INTO cdm_supply_order (id, tenant_id, erp_source_id, product_id, supplier_id,
                                                  quantity_ordered, expected_date, status)
                    VALUES (:id, :tid, :eid, :pid, :sid, :qty, :exp_date, 'confirmed')
                    ON CONFLICT DO NOTHING
                """),
                {"id": uuid.uuid4(), "tid": tenant_id,
                 "eid": f"PO-{i+1:04d}",
                 "pid": product_ids[(i + 1) % len(product_ids)],
                 "sid": supplier_ids[i % len(supplier_ids)],
                 "qty": 500 + i * 200,
                 "exp_date": datetime.now(UTC) + timedelta(days=(i + 1) * 7)},
            )

        await session.commit()
        print("Seed data created successfully")


if __name__ == "__main__":
    asyncio.run(seed())
