"""Notification center for IPE — multi-channel delivery.

Supports: in-app, email, SMS, push notifications.
Template-based with priority levels and delivery tracking.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

logger = logging.getLogger("ipe.notifications")


class NotificationChannel(StrEnum):
    IN_APP = "in_app"
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"


class NotificationPriority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class NotificationStatus(StrEnum):
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    READ = "read"


@dataclass
class NotificationTemplate:
    template_id: str
    name: str
    subject: str
    body_template: str
    channels: list[NotificationChannel]
    priority: NotificationPriority = NotificationPriority.MEDIUM
    variables: list[str] = field(default_factory=list)


@dataclass
class Notification:
    notification_id: str
    tenant_id: str
    user_id: str
    template_id: str
    subject: str
    body: str
    channel: NotificationChannel
    priority: NotificationPriority
    status: NotificationStatus = NotificationStatus.PENDING
    created_at: str = ""
    sent_at: str = ""
    read_at: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.created_at:
            self.created_at = datetime.now(UTC).isoformat()


TEMPLATES: dict[str, NotificationTemplate] = {
    "mo_completed": NotificationTemplate(
        template_id="mo_completed",
        name="Manufacturing Order Completed",
        subject="MO {mo_id} Completed Successfully",
        body_template="Manufacturing order {mo_id} for {item_name} has been completed at {location}.",
        channels=[NotificationChannel.IN_APP, NotificationChannel.EMAIL],
        priority=NotificationPriority.MEDIUM,
        variables=["mo_id", "item_name", "location"],
    ),
    "quality_alert": NotificationTemplate(
        template_id="quality_alert",
        name="Quality Alert",
        subject="Quality Alert: {severity} issue detected",
        body_template="A {severity} quality issue has been detected on line {line}. Details: {description}",
        channels=[NotificationChannel.IN_APP, NotificationChannel.EMAIL, NotificationChannel.SMS],
        priority=NotificationPriority.HIGH,
        variables=["severity", "line", "description"],
    ),
    "capacity_warning": NotificationTemplate(
        template_id="capacity_warning",
        name="Capacity Warning",
        subject="Capacity Warning: {workcenter} at {utilization}%",
        body_template="Work center {workcenter} is at {utilization}% capacity. Consider rescheduling.",
        channels=[NotificationChannel.IN_APP],
        priority=NotificationPriority.MEDIUM,
        variables=["workcenter", "utilization"],
    ),
    "system_alert": NotificationTemplate(
        template_id="system_alert",
        name="System Alert",
        subject="System Alert: {alert_name}",
        body_template="System alert triggered: {alert_name}. Severity: {severity}. Details: {details}",
        channels=[NotificationChannel.IN_APP, NotificationChannel.EMAIL, NotificationChannel.PUSH],
        priority=NotificationPriority.CRITICAL,
        variables=["alert_name", "severity", "details"],
    ),
}


class NotificationCenter:
    def __init__(self) -> None:
        self._notifications: list[Notification] = []
        self._templates = TEMPLATES.copy()

    def send_notification(
        self,
        tenant_id: str,
        user_id: str,
        template_id: str,
        channel: NotificationChannel,
        variables: dict[str, str] | None = None,
        priority_override: NotificationPriority | None = None,
    ) -> Notification:
        template = self._templates.get(template_id)
        if not template:
            raise ValueError(f"Unknown template: {template_id}")

        if channel not in template.channels:
            logger.warning("Channel %s not configured for template %s", channel.value, template_id)

        subject = template.subject
        body = template.body_template
        if variables:
            for key, value in variables.items():
                subject = subject.replace(f"{{{key}}}", value)
                body = body.replace(f"{{{key}}}", value)

        notification = Notification(
            notification_id=f"notif_{tenant_id}_{datetime.now(UTC).timestamp()}",
            tenant_id=tenant_id,
            user_id=user_id,
            template_id=template_id,
            subject=subject,
            body=body,
            channel=channel,
            priority=priority_override or template.priority,
        )

        self._notifications.append(notification)
        notification.status = NotificationStatus.SENT
        notification.sent_at = datetime.now(UTC).isoformat()

        logger.info("Notification sent: id=%s channel=%s priority=%s subject=%s",
                    notification.notification_id, channel.value, notification.priority.value, subject)

        return notification

    def get_user_notifications(
        self,
        tenant_id: str,
        user_id: str,
        unread_only: bool = False,
    ) -> list[Notification]:
        results = [n for n in self._notifications if n.tenant_id == tenant_id and n.user_id == user_id]
        if unread_only:
            results = [n for n in results if n.status != NotificationStatus.READ]
        return sorted(results, key=lambda n: n.created_at, reverse=True)

    def mark_read(self, notification_id: str) -> bool:
        for notif in self._notifications:
            if notif.notification_id == notification_id:
                notif.status = NotificationStatus.READ
                notif.read_at = datetime.now(UTC).isoformat()
                return True
        return False

    def get_unread_count(self, tenant_id: str, user_id: str) -> int:
        return len([
            n for n in self._notifications
            if n.tenant_id == tenant_id and n.user_id == user_id and n.status != NotificationStatus.READ
        ])
