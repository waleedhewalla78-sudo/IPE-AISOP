from app.core.validator import UploadValidator
from app.core.wizard import OnboardingWizard


def test_validate_product_master_csv():
    content = b"product_code,name,type,uom\nFG-DT100,Transformer,finished,unit\n"
    result = UploadValidator().validate("product_master", content, "products.csv")
    assert result.stage_1_structure["status"] == "pass"
    assert result.accepted == 1
    assert result.rejected == 0
    assert "A2" in result.agents_triggered or "A4" in result.agents_triggered


def test_validate_missing_columns():
    content = b"product_code,name\nFG-1,X\n"
    result = UploadValidator().validate("product_master", content, "bad.csv")
    assert result.stage_1_structure["status"] == "fail"


def test_wizard_phase_completion():
    wiz = OnboardingWizard()
    tenant = "t1"
    status = wiz.status(tenant)
    assert status["current_phase"] == 1
    done = wiz.complete_phase(tenant, 1)
    assert done["phase_completed"] == 1
    assert done["agents_newly_activated"]
    assert wiz.status(tenant)["current_phase"] == 2
