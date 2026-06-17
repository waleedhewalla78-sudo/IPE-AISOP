"""Kafka event consumers for alert-svc.

Listens to ipe.mo.feasibility_scored and ipe.workcenter.status_changed
events, evaluates alert rules, and dispatches notifications.
"""

import logging
from contextlib import suppress

from app.core.notifier import send_alert_notification
from app.core.rules import evaluate_event

_logger = logging.getLogger(__name__)

_topics = ["ipe.mo.feasibility_scored", "ipe.workcenter.status_changed"]
_consumers: list = []


async def start_consumers():
    try:
        from ipe_shared.events.consumer import create_consumer

        for topic in _topics:
            consumer = create_consumer("alert-svc", topic)
            _consumers.append(consumer)
        _logger.info(
            "Alert consumers started for topics: %s", _topics
        )
    except Exception as exc:
        _logger.warning("Could not start Kafka consumers (Kafka may not be available): %s", exc)


async def stop_consumers():
    for c in _consumers:
        with suppress(Exception):
            await c.stop()
    _consumers.clear()


async def handle_event(event_type: str, payload: dict) -> None:
    alerts = evaluate_event(event_type, payload)
    for alert in alerts:
        await send_alert_notification(alert)
