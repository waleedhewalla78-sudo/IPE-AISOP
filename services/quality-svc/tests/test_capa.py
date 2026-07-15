"""A10 CAPA unit tests."""

from app.core.capa import clear_capa_store, create_capa, list_capas


def setup_function():
    clear_capa_store()


def test_create_capa_has_verify_windows():
    capa = create_capa(mo_id="MO-ST-008", defect_type="winding", severity="high")
    assert capa["capa_id"].startswith("CAPA-")
    assert capa["status"] == "open"
    assert "d30" in capa["verify_windows"]
    assert list_capas(status="open")


def test_list_filters_status():
    create_capa(mo_id="MO-1", defect_type="surface")
    create_capa(mo_id="MO-2", defect_type="weld")
    assert len(list_capas()) == 2
