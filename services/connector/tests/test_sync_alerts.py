"""Tests for sync failure alert hook."""

from unittest.mock import patch

from app.core.sync_alerts import notify_sync_failure


def test_notify_sync_failure_logs_without_webhook(caplog):
    with patch.dict("os.environ", {"ODOO_SYNC_ALERT_WEBHOOK": ""}, clear=False):
        notify_sync_failure(
            tenant_id="test-tenant",
            sync_run_id="run-1",
            status="failed",
            error_summary="connection timeout",
        )
    assert any("odoo_sync_failure" in r.message for r in caplog.records)


def test_notify_sync_failure_posts_webhook():
    with patch.dict("os.environ", {"ODOO_SYNC_ALERT_WEBHOOK": "http://example.com/hook"}, clear=False):
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.return_value.__enter__.return_value.status = 200
            notify_sync_failure(
                tenant_id="test-tenant",
                sync_run_id="run-1",
                status="partial",
                error_summary="some entities failed",
            )
            mock_urlopen.assert_called_once()
