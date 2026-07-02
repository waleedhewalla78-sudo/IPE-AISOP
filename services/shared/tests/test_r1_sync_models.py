"""Unit tests for Release 1 sync audit models (migration 036)."""

from ipe_shared.models.data_quality_flag import DATA_QUALITY_FLAG_CODES, DataQualityFlag
from ipe_shared.models.manufacturing_order import ManufacturingOrder
from ipe_shared.models.sync_run import SYNC_RUN_STATUSES, SyncRun


def test_sync_run_table_name():
    assert SyncRun.__tablename__ == "cdm_sync_run"


def test_sync_run_status_constraint_present():
    names = {c.name for c in SyncRun.__table_args__ if hasattr(c, "name")}
    assert "ck_sync_run_status" in names


def test_sync_run_status_values_cover_expected():
    assert "running" in SYNC_RUN_STATUSES
    assert "success" in SYNC_RUN_STATUSES
    assert "failed" in SYNC_RUN_STATUSES


def test_data_quality_flag_table_name():
    assert DataQualityFlag.__tablename__ == "cdm_data_quality_flag"


def test_data_quality_flag_codes_include_odoo_gaps():
    assert "MISSING_BOM" in DATA_QUALITY_FLAG_CODES
    assert "MISSING_ROUTING" in DATA_QUALITY_FLAG_CODES
    assert "SYNC_CONFLICT" in DATA_QUALITY_FLAG_CODES


def test_manufacturing_order_erp_sync_columns():
    col_names = {c.name for c in ManufacturingOrder.__table__.columns}
    assert "erp_last_update" in col_names
    assert "erp_synced_at" in col_names
    assert "sync_conflict" in col_names
