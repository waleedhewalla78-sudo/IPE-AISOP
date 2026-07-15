from app.core.executive_brief import SopExecutiveBrief


def test_executive_brief_structure():
    brief = SopExecutiveBrief().generate()
    assert "headline" in brief
    assert "demand_review" in brief
    assert "decisions_required" in brief
    assert len(brief["decisions_required"]) >= 1
