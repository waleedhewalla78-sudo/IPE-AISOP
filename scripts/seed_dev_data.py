"""Seed development data for MDR and RLS isolation testing.

Creates:
- tenant_a (clean data): BOM completeness = 90%, lead time accuracy = 85% — passes MDR gates
- tenant_b (dirty data): BOM completeness = 65% — triggers MDR_GATE_FAILED
- 2 users per tenant for RLS isolation testing
"""

import os
import sys
from uuid import UUID, uuid4

TENANT_A_ID = UUID("a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11")
TENANT_B_ID = UUID("b0eebc99-9c0b-4ef8-bb6d-6bb9bd380b22")

PRODUCT_IDS_A = [uuid4() for _ in range(10)]
PRODUCT_IDS_B = [uuid4() for _ in range(10)]


def get_dsn() -> str:
    return os.environ.get(
        "IPE_DATABASE_URL_SYNC",
        "postgresql://ipe:ipe_dev_pass@localhost:5432/ipe_dev",
    )


def make_sql():
    sql = []

    # Cleanup
    sql.append("DELETE FROM cdm_mdr_score;")
    sql.append("DELETE FROM cdm_demand_line;")
    sql.append("DELETE FROM cdm_bom_line;")
    sql.append("DELETE FROM cdm_bill_of_material;")
    sql.append("DELETE FROM cdm_product;")
    sql.append("DELETE FROM cdm_user;")
    sql.append("DELETE FROM cdm_tenant;")

    # Tenants
    sql.append(f"""
        INSERT INTO cdm_tenant (id, name, tier, erp_type, autonomy_mode)
        VALUES ('{TENANT_A_ID}', 'Tenant A - Clean Data', 'professional', 'odoo', 'shadow');
    """)
    sql.append(f"""
        INSERT INTO cdm_tenant (id, name, tier, erp_type, autonomy_mode)
        VALUES ('{TENANT_B_ID}', 'Tenant B - Dirty Data', 'starter', 'odoo', 'shadow');
    """)

    # Users - 2 per tenant
    for tid, name in [(TENANT_A_ID, "A"), (TENANT_B_ID, "B")]:
        sql.append(f"""
            INSERT INTO cdm_user (tenant_id, email, role)
            VALUES ('{tid}', 'admin@tenant{name.lower()}.com', 'admin');
        """)
        sql.append(f"""
            INSERT INTO cdm_user (tenant_id, email, role)
            VALUES ('{tid}', 'planner@tenant{name.lower()}.com', 'planner');
        """)

    # Tenant A - 10 products (6 manufactured, 4 purchased), 90% BOM completeness, 85% lead time accuracy
    # 6 manufactured: 5 with active BOMs (83.3% → but some purchased also have lead times)
    for i, pid in enumerate(PRODUCT_IDS_A):
        source = "manufactured" if i < 6 else "purchased"
        lead_time = 5.0 if i < 8 else None  # 8/10 = 80% have lead time
        if lead_time is None:
            lt_sql = "NULL"
        else:
            lt_sql = str(lead_time)
        sql.append(f"""
            INSERT INTO cdm_product (id, tenant_id, erp_source_id, name, source_type, lead_time_days)
            VALUES ('{pid}', '{TENANT_A_ID}', 'PROD-A-{i:03d}', 'Product A-{i}', '{source}', {lt_sql});
        """)

    # Tenant A BOMs - 5 of 6 manufactured products have active BOMs (83.3% BOM completeness)
    for i in range(5):  # 5 BOMs for first 5 manufactured products
        bom_id = uuid4()
        sql.append(f"""
            INSERT INTO cdm_bill_of_material (id, tenant_id, product_id, is_active)
            VALUES ('{bom_id}', '{TENANT_A_ID}', '{PRODUCT_IDS_A[i]}', true);
        """)
        # Each BOM has 2 lines
        comp_idx = (i % 4) + 6  # use purchased products as components
        sql.append(f"""
            INSERT INTO cdm_bom_line (tenant_id, bom_id, component_id, quantity_per)
            VALUES ('{TENANT_A_ID}', '{bom_id}', '{PRODUCT_IDS_A[comp_idx]}', 2.0);
        """)
        sql.append(f"""
            INSERT INTO cdm_bom_line (tenant_id, bom_id, component_id, quantity_per)
            VALUES ('{TENANT_A_ID}', '{bom_id}', '{PRODUCT_IDS_A[(comp_idx + 1) % 4 + 6]}', 1.5);
        """)

    # Tenant B - 10 products (6 manufactured, 4 purchased), 65% BOM completeness, 55% lead time accuracy
    for i, pid in enumerate(PRODUCT_IDS_B):
        source = "manufactured" if i < 6 else "purchased"
        lead_time = 5.0 if i < 6 else None  # 6/10 = 60% have lead time
        if lead_time is None:
            lt_sql = "NULL"
        else:
            lt_sql = str(lead_time)
        sql.append(f"""
            INSERT INTO cdm_product (id, tenant_id, erp_source_id, name, source_type, lead_time_days)
            VALUES ('{pid}', '{TENANT_B_ID}', 'PROD-B-{i:03d}', 'Product B-{i}', '{source}', {lt_sql});
        """)

    # Tenant B BOMs - 4 of 6 manufactured have active BOMs
    # 4/6 = 66.7% BOM completeness (under 80% threshold)
    for i in range(4):
        bom_id = uuid4()
        sql.append(f"""
            INSERT INTO cdm_bill_of_material (id, tenant_id, product_id, is_active)
            VALUES ('{bom_id}', '{TENANT_B_ID}', '{PRODUCT_IDS_B[i]}', true);
        """)
        comp_idx = (i % 4) + 6
        sql.append(f"""
            INSERT INTO cdm_bom_line (tenant_id, bom_id, component_id, quantity_per)
            VALUES ('{TENANT_B_ID}', '{bom_id}', '{PRODUCT_IDS_B[comp_idx]}', 2.0);
        """)

    return "\n".join(sql)


def main():
    dsn = get_dsn()
    print(f"Connecting to {dsn}")
    import psycopg2

    conn = psycopg2.connect(dsn)
    conn.autocommit = True
    cur = conn.cursor()
    sql = make_sql()
    cur.execute(sql)
    print("Seed data loaded successfully.")
    print(f"  Tenant A (clean):  {TENANT_A_ID}")
    print(f"  Tenant B (dirty): {TENANT_B_ID}")
    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
