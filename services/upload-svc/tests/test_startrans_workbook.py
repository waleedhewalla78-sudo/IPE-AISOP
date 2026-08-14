"""Minimal unit test for Star Trans workbook sheet list."""

from app.core.startrans_workbook import EXPECTED_SHEETS, preview_counts, parse_workbook


def test_expected_sheets_count():
    assert len(EXPECTED_SHEETS) == 24


def test_parse_rejects_non_xlsx():
    result = parse_workbook(b"not-excel", "notes.csv")
    assert result.valid is False
    assert any("Unsupported" in e for e in result.errors)
    preview = preview_counts(result)
    assert preview["will_insert"] == 0
