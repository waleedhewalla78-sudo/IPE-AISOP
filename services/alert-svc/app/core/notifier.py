"""SMTP-based email notification dispatcher for alerts."""

import logging
from contextlib import asynccontextmanager, suppress

from app.config import settings
from app.core.rules import Alert

_logger = logging.getLogger(__name__)


@asynccontextmanager
async def _smtp_connection():
    import aiosmtplib

    smtp = aiosmtplib.SMTP(hostname=settings.SMTP_HOST, port=settings.SMTP_PORT)
    await smtp.connect()
    if settings.SMTP_USERNAME:
        await smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
    try:
        yield smtp
    finally:
        with suppress(Exception):
            await smtp.quit()


def _format_email(alert: Alert) -> str:
    return (
        f"Subject: IPE Alert [{alert.severity.upper()}] {alert.title}\n"
        f"To: {settings.ALERT_RECIPIENT}\n"
        f"From: {settings.FROM_EMAIL}\n"
        f"MIME-Version: 1.0\n"
        f"Content-Type: text/plain; charset=utf-8\n\n"
        f"Alert Type: {alert.alert_type}\n"
        f"Severity: {alert.severity}\n"
        f"Description: {alert.description}\n"
        f"Entity: {alert.entity_id or 'N/A'}\n"
        f"Metadata: {alert.metadata}\n"
    )


async def send_alert_notification(alert: Alert) -> bool:
    try:
        email_body = _format_email(alert)
        async with _smtp_connection() as smtp:
            await smtp.sendmail(
                settings.FROM_EMAIL,
                settings.ALERT_RECIPIENT,
                email_body.encode("utf-8"),
            )
        _logger.info("Alert sent: %s", alert.title)
        return True
    except Exception as exc:
        _logger.error("Failed to send alert notification: %s", exc)
        return False
