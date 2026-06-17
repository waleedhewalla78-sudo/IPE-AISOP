from unittest.mock import AsyncMock, patch

from app.core.notifier import send_alert_notification
from app.core.rules import Alert


@patch("app.core.notifier._smtp_connection")
async def test_send_alert_success(mock_smtp):
    mock_smtp.return_value.__aenter__.return_value = AsyncMock()
    alert = Alert(
        alert_type="feasibility_critical",
        severity="high",
        title="Test Alert",
        description="Test description",
        entity_id="MO-001",
        metadata={"score": 50},
    )
    result = await send_alert_notification(alert)
    assert result is True


@patch("app.core.notifier._smtp_connection", side_effect=ConnectionError("SMTP down"))
async def test_send_alert_failure(mock_smtp):
    alert = Alert(
        alert_type="feasibility_critical",
        severity="high",
        title="Test Alert",
        description="Test description",
    )
    result = await send_alert_notification(alert)
    assert result is False
