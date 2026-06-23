from app.core.response_formatter import format_structured_response, is_llm_error


def test_is_llm_error():
    assert is_llm_error("LLM error: all providers unavailable")
    assert not is_llm_error("Widget A: 150 units")


def test_format_inventory_response():
    data = {
        "items": [
            {
                "name": "Widget A",
                "internal_ref": "WGT-A-100",
                "uom": "unit",
                "qty_on_hand": 150,
                "qty_reserved": 20,
                "qty_available": 130,
            }
        ]
    }
    text = format_structured_response("material_status", data)
    assert text is not None
    assert "Widget A" in text
    assert "130 unit available" in text


def test_format_inventory_empty():
    text = format_structured_response("material_status", {"items": []})
    assert text is not None
    assert "No inventory records" in text
