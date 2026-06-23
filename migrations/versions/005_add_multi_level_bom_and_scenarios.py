"""Add multi-level BOM support, phantom BOMs, and scenario sandbox tables

Revision ID: 005
Revises: 004
Create Date: 2026-06-17
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade():
    # Multi-level BOM support
    op.add_column("cdm_bill_of_material", sa.Column("parent_bom_id", UUID, sa.ForeignKey("cdm_bill_of_material.id")))
    op.add_column("cdm_bill_of_material", sa.Column("bom_level", sa.Integer, server_default="0"))
    op.add_column("cdm_bill_of_material", sa.Column("is_phantom", sa.Boolean, server_default="false"))
    op.create_index("ix_bom_parent", "cdm_bill_of_material", ["parent_bom_id"])

    # Routing operation hierarchy
    op.add_column("cdm_routing_operation", sa.Column("parent_operation_id", UUID, sa.ForeignKey("cdm_routing_operation.id")))
    op.add_column("cdm_routing_operation", sa.Column("bom_level", sa.Integer, server_default="0"))
    op.add_column("cdm_routing_operation", sa.Column("transfer_time_mins", sa.Numeric(10, 2), server_default="0"))
    op.create_index("ix_routing_parent", "cdm_routing_operation", ["parent_operation_id"])

    # Scenario sandbox tables
    op.create_table(
        "cdm_scenario",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tenant_id", UUID, sa.ForeignKey("cdm_tenant.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("base_scenario_id", UUID),
        sa.Column("status", sa.String(24), server_default="active"),
        sa.Column("created_by", sa.String(128)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_scenario_tenant", "cdm_scenario", ["tenant_id", "status"])

    op.create_table(
        "cdm_scenario_demand",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("scenario_id", UUID, sa.ForeignKey("cdm_scenario.id", ondelete="CASCADE"), nullable=False),
        sa.Column("original_demand_id", UUID, nullable=False),
        sa.Column("data", JSONB, nullable=False),
    )
    op.create_index("ix_scenario_demand_scenario", "cdm_scenario_demand", ["scenario_id"])

    op.create_table(
        "cdm_scenario_supply",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("scenario_id", UUID, sa.ForeignKey("cdm_scenario.id", ondelete="CASCADE"), nullable=False),
        sa.Column("original_supply_id", UUID, nullable=False),
        sa.Column("data", JSONB, nullable=False),
    )
    op.create_index("ix_scenario_supply_scenario", "cdm_scenario_supply", ["scenario_id"])

    op.create_table(
        "cdm_scenario_resource",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("scenario_id", UUID, sa.ForeignKey("cdm_scenario.id", ondelete="CASCADE"), nullable=False),
        sa.Column("original_resource_id", UUID, nullable=False),
        sa.Column("data", JSONB, nullable=False),
    )
    op.create_index("ix_scenario_resource_scenario", "cdm_scenario_resource", ["scenario_id"])

    # Reconciliation / ML tracking (extend existing cdm_duration_prediction table)
    op.add_column("cdm_duration_prediction", sa.Column("scenario_id", UUID))
    op.add_column("cdm_duration_prediction", sa.Column("mae_30d", sa.Numeric(5, 4)))
    op.add_column("cdm_duration_prediction", sa.Column("drift_detected", sa.Boolean, server_default="false"))

    # NLP root cause analysis
    op.create_table(
        "cdm_delay_root_cause",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tenant_id", UUID, sa.ForeignKey("cdm_tenant.id", ondelete="CASCADE"), nullable=False),
        sa.Column("delay_event_id", UUID, sa.ForeignKey("cdm_delay_event.id")),
        sa.Column("source_text", sa.Text, nullable=False),
        sa.Column("primary_category", sa.String(50), nullable=False),
        sa.Column("secondary_categories", JSONB),
        sa.Column("confidence", sa.Numeric(5, 4)),
        sa.Column("extracted_by", sa.String(50)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_delay_root_cause_tenant", "cdm_delay_root_cause", ["tenant_id", "created_at"])
    op.create_index("ix_delay_root_cause_event", "cdm_delay_root_cause", ["delay_event_id"])


def downgrade():
    op.drop_table("cdm_delay_root_cause")
    op.drop_column("cdm_duration_prediction", "drift_detected")
    op.drop_column("cdm_duration_prediction", "mae_30d")
    op.drop_column("cdm_duration_prediction", "scenario_id")
    op.drop_table("cdm_scenario_resource")
    op.drop_table("cdm_scenario_supply")
    op.drop_table("cdm_scenario_demand")
    op.drop_table("cdm_scenario")
    op.drop_index("ix_routing_parent", table_name="cdm_routing_operation")
    op.drop_column("cdm_routing_operation", "transfer_time_mins")
    op.drop_column("cdm_routing_operation", "bom_level")
    op.drop_column("cdm_routing_operation", "parent_operation_id")
    op.drop_index("ix_bom_parent", table_name="cdm_bill_of_material")
    op.drop_column("cdm_bill_of_material", "is_phantom")
    op.drop_column("cdm_bill_of_material", "bom_level")
    op.drop_column("cdm_bill_of_material", "parent_bom_id")