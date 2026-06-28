"""v8 Phase 1: copilot sessions, demand forecasts/signals, scenario KPI results

Revision ID: 029
Revises: 028
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "029"
down_revision = "028"
branch_labels = None
depends_on = None


def _rls(table: str) -> None:
    op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
    op.execute(
        f"CREATE POLICY tenant_isolation ON {table} "
        "USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)"
    )


def upgrade():
    op.create_table(
        "cdm_copilot_session",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tenant_id", UUID, sa.ForeignKey("cdm_tenant.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", UUID, sa.ForeignKey("cdm_user.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(32), nullable=False),
        sa.Column("context_jsonb", JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_copilot_session_tenant_user", "cdm_copilot_session", ["tenant_id", "user_id"])
    _rls("cdm_copilot_session")

    op.create_table(
        "cdm_demand_signal",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tenant_id", UUID, sa.ForeignKey("cdm_tenant.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_type", sa.String(32), nullable=False),
        sa.Column("source_id", sa.String(128)),
        sa.Column("product_id", UUID, sa.ForeignKey("cdm_product.id")),
        sa.Column("location_id", UUID),
        sa.Column("signal_ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("value", sa.Numeric(14, 4), nullable=False),
        sa.Column("quality_score", sa.Numeric(5, 4), server_default="1.0"),
        sa.Column("metadata_jsonb", JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_demand_signal_tenant_product", "cdm_demand_signal", ["tenant_id", "product_id", "signal_ts"])
    _rls("cdm_demand_signal")

    op.create_table(
        "cdm_demand_forecast",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tenant_id", UUID, sa.ForeignKey("cdm_tenant.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_id", UUID, sa.ForeignKey("cdm_product.id"), nullable=False),
        sa.Column("location_id", UUID),
        sa.Column("horizon_type", sa.String(16), nullable=False, server_default="short"),
        sa.Column("forecast_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("value", sa.Numeric(14, 4), nullable=False),
        sa.Column("lower_bound", sa.Numeric(14, 4)),
        sa.Column("upper_bound", sa.Numeric(14, 4)),
        sa.Column("model_version", sa.String(32), server_default="ses-v1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index(
        "ix_demand_forecast_lookup",
        "cdm_demand_forecast",
        ["tenant_id", "product_id", "horizon_type", "forecast_date"],
    )
    _rls("cdm_demand_forecast")

    op.create_table(
        "cdm_scenario_parameter",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tenant_id", UUID, sa.ForeignKey("cdm_tenant.id", ondelete="CASCADE"), nullable=False),
        sa.Column("scenario_id", UUID, sa.ForeignKey("cdm_scenario.id", ondelete="CASCADE"), nullable=False),
        sa.Column("parameter_key", sa.String(64), nullable=False),
        sa.Column("parameter_value", sa.String(256), nullable=False),
        sa.Column("data_type", sa.String(16), server_default="string"),
        sa.Column("description", sa.Text),
    )
    op.create_index("ix_scenario_param_scenario", "cdm_scenario_parameter", ["scenario_id", "parameter_key"])
    _rls("cdm_scenario_parameter")

    op.create_table(
        "cdm_scenario_result",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tenant_id", UUID, sa.ForeignKey("cdm_tenant.id", ondelete="CASCADE"), nullable=False),
        sa.Column("scenario_id", UUID, sa.ForeignKey("cdm_scenario.id", ondelete="CASCADE"), nullable=False),
        sa.Column("kpi_key", sa.String(64), nullable=False),
        sa.Column("kpi_value", sa.Numeric(14, 4), nullable=False),
        sa.Column("unit", sa.String(16), server_default="count"),
        sa.Column("computed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_scenario_result_scenario", "cdm_scenario_result", ["scenario_id", "kpi_key"])
    _rls("cdm_scenario_result")


def downgrade():
    op.drop_table("cdm_scenario_result")
    op.drop_table("cdm_scenario_parameter")
    op.drop_table("cdm_demand_forecast")
    op.drop_table("cdm_demand_signal")
    op.drop_table("cdm_copilot_session")
