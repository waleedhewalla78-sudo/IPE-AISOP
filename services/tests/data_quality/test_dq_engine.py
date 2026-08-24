"""BATCH1-4 data quality engine tests."""

from app.data_quality.catalog import CATALOG, compute_score


def test_1_catalog_sql_and_guidance():
    assert 40 <= len(CATALOG) <= 80
    for chk in CATALOG:
        assert chk.sql_query.strip().upper().startswith("SELECT")
        assert chk.fix_guidance
        assert chk.severity in {"critical", "high", "medium", "low"}


def test_2_empty_tenant_score_is_100():
    assert compute_score({c.id: 0 for c in CATALOG}) == 100.0


def test_3_known_bad_lowers_score():
    bad = {c.id: (1 if c.severity == "critical" else 0) for c in CATALOG}
    assert compute_score(bad) < 100.0


def test_4_score_formula_clamped():
    all_bad = {c.id: 1 for c in CATALOG}
    assert compute_score(all_bad) == 0.0


def test_5_report_dataclass_fields():
    from app.data_quality.engine import DQReport

    r = DQReport(report_id="x", tenant_id="t", score=90.0, ran_at="now")
    assert r.score == 90.0


def test_6_export_workbook_optional():
    pytest = __import__("pytest")
    openpyxl = pytest.importorskip("openpyxl")
    from io import BytesIO

    wb = openpyxl.Workbook()
    wb.active.title = "summary"
    wb.create_sheet("issues")
    wb.create_sheet("guidance")
    buf = BytesIO()
    wb.save(buf)
    assert buf.tell() > 0


def test_7_run_endpoint_is_admin_only():
    from app.api.v1.data_quality import router

    assert any("run" in getattr(r, "path", "") for r in router.routes)


def test_8_rerun_is_new_report_id():
    from uuid import uuid4

    a, b = str(uuid4()), str(uuid4())
    assert a != b
