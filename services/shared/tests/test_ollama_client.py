"""Phase 8 — Ollama client health + rule-based degrade."""

from unittest.mock import MagicMock, patch

from ipe_shared.llm.ollama_client import (
    AI_UNAVAILABLE_BANNER,
    OllamaClient,
    generate_agent_explanation,
)


def test_health_unreachable_degrades():
    client = OllamaClient(base_url="http://127.0.0.1:9", timeout_s=0.2)
    health = client.check_health()
    assert health.available is False
    assert health.degrade_mode is True
    flag = health.to_api_flag()
    assert flag["show_amber_banner"] is True
    assert AI_UNAVAILABLE_BANNER in flag["banner_message_en"]


def test_generate_degrades_when_down():
    client = OllamaClient(base_url="http://127.0.0.1:9", timeout_s=0.2)
    result = client.generate("MO at risk due to capacity", locale="en")
    assert result.degraded is True
    assert result.source == "rule_based"
    assert "Rule-based" in result.text or "unavailable" in result.text.lower()


def test_generate_arabic_rule_based():
    client = OllamaClient(base_url="http://127.0.0.1:9", timeout_s=0.2)
    result = client.generate("capacity overload", locale="ar")
    assert result.degraded is True
    assert "القواعد" in result.text or "غير متاح" in result.text


@patch("ipe_shared.llm.ollama_client.urllib.request.urlopen")
def test_health_ok_when_tags_return(mock_urlopen):
    payload = b'{"models":[{"name":"llama3.1:latest"}]}'
    resp = MagicMock()
    resp.read.return_value = payload
    resp.__enter__.return_value = resp
    resp.__exit__.return_value = False
    mock_urlopen.return_value = resp

    client = OllamaClient(base_url="http://ollama.test:11434", timeout_s=1.0)
    health = client.check_health()
    assert health.available is True
    assert "llama3.1:latest" in health.models
    assert health.to_api_flag()["show_amber_banner"] is False


def test_generate_agent_explanation_degrades():
    client = OllamaClient(base_url="http://127.0.0.1:9", timeout_s=0.2)
    result = generate_agent_explanation("A4", {"mo_id": "MO-1"}, client=client)
    assert result.degraded is True
