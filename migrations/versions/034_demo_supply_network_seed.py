"""Seed demo supply network: 4 plants + 6 transfer lanes for demo tenant.

Revision ID: 034
Revises: 033
"""
from alembic import op

revision = "034"
down_revision = "033"
branch_labels = None
depends_on = None

TENANT = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"

PLANTS = [
    ("f1eebc99-9c0b-4ef8-bb6d-6bb9bd380001", "Plant-Hamburg", "DEMO-HAMBURG", 53.5511, 9.9937, 16.0),
    ("f1eebc99-9c0b-4ef8-bb6d-6bb9bd380002", "Plant-Shanghai", "DEMO-SHANGHAI", 31.2304, 121.4737, 20.0),
    ("f1eebc99-9c0b-4ef8-bb6d-6bb9bd380003", "DC-Rotterdam", "DEMO-ROTTERDAM", 51.9244, 4.4777, 24.0),
    ("f1eebc99-9c0b-4ef8-bb6d-6bb9bd380004", "Plant-Chicago", "DEMO-CHICAGO", 41.8781, -87.6298, 16.0),
]

ROUTES = [
    ("a1eebc99-9c0b-4ef8-bb6d-6bb9bd380001", "f1eebc99-9c0b-4ef8-bb6d-6bb9bd380001", "f1eebc99-9c0b-4ef8-bb6d-6bb9bd380003", "sea", 72.0, 2.5, 5000),
    ("a1eebc99-9c0b-4ef8-bb6d-6bb9bd380002", "f1eebc99-9c0b-4ef8-bb6d-6bb9bd380002", "f1eebc99-9c0b-4ef8-bb6d-6bb9bd380003", "sea", 480.0, 4.0, 8000),
    ("a1eebc99-9c0b-4ef8-bb6d-6bb9bd380003", "f1eebc99-9c0b-4ef8-bb6d-6bb9bd380003", "f1eebc99-9c0b-4ef8-bb6d-6bb9bd380004", "sea", 336.0, 3.2, 6000),
    ("a1eebc99-9c0b-4ef8-bb6d-6bb9bd380004", "f1eebc99-9c0b-4ef8-bb6d-6bb9bd380001", "f1eebc99-9c0b-4ef8-bb6d-6bb9bd380004", "air", 120.0, 8.5, 2000),
    ("a1eebc99-9c0b-4ef8-bb6d-6bb9bd380005", "f1eebc99-9c0b-4ef8-bb6d-6bb9bd380004", "f1eebc99-9c0b-4ef8-bb6d-6bb9bd380001", "rail", 168.0, 1.8, 10000),
    ("a1eebc99-9c0b-4ef8-bb6d-6bb9bd380006", "f1eebc99-9c0b-4ef8-bb6d-6bb9bd380002", "f1eebc99-9c0b-4ef8-bb6d-6bb9bd380004", "air", 96.0, 9.0, 1500),
]


def upgrade():
    for pid, name, code, lat, lon, cap in PLANTS:
        op.execute(
            f"""
            INSERT INTO cdm_plant (id, tenant_id, name, code, latitude, longitude, capacity_hours_per_day, is_active)
            VALUES ('{pid}', '{TENANT}', '{name}', '{code}', {lat}, {lon}, {cap}, true)
            ON CONFLICT (code) DO UPDATE SET
                tenant_id = EXCLUDED.tenant_id,
                name = EXCLUDED.name,
                latitude = EXCLUDED.latitude,
                longitude = EXCLUDED.longitude,
                capacity_hours_per_day = EXCLUDED.capacity_hours_per_day,
                is_active = true
            """
        )
    for rid, origin, dest, mode, hours, cost, capacity in ROUTES:
        op.execute(
            f"""
            INSERT INTO cdm_transfer_route (
                id, tenant_id, origin_plant_id, destination_plant_id,
                transport_mode, transit_time_hours, cost_per_unit, capacity_units, is_active
            )
            VALUES (
                '{rid}', '{TENANT}', '{origin}', '{dest}',
                '{mode}', {hours}, {cost}, {capacity}, true
            )
            ON CONFLICT (id) DO NOTHING
            """
        )


def downgrade():
    op.execute(f"DELETE FROM cdm_transfer_route WHERE tenant_id = '{TENANT}' AND id::text LIKE 'a1eebc99%'")
    op.execute(
        f"DELETE FROM cdm_plant WHERE tenant_id = '{TENANT}' AND code IN "
        "('DEMO-HAMBURG','DEMO-SHANGHAI','DEMO-ROTTERDAM','DEMO-CHICAGO')"
    )
