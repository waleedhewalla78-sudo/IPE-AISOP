"""Upload-svc Phase 8 file type schemas."""

from app.core.validator import FILE_SCHEMAS, UploadValidator, normalize_file_type


def test_phase8_schemas_present():
    for key in ("demand_forecast", "quality_results", "sop_sales_input"):
        assert key in FILE_SCHEMAS
        assert "required" in FILE_SCHEMAS[key]
        assert FILE_SCHEMAS[key]["phase"] == 8


def test_aliases():
    assert normalize_file_type("forecast") == "demand_forecast"
    assert normalize_file_type("quality_inspection") == "quality_results"


def test_validate_demand_forecast_csv():
    content = b"product_code,period,forecast_qty\nFG-DT100,2026-08,120\n"
    result = UploadValidator().validate("demand_forecast", content, "forecast.csv")
    assert result.accepted >= 1
    assert result.rejected == 0
