"""Notification center API endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from ipe_shared.notifications.center import (
    NotificationCenter,
    NotificationChannel,
    NotificationPriority,
)

router = APIRouter(prefix="/notifications", tags=["notifications"])


class SendNotificationRequest(BaseModel):
    user_id: str = Field(..., min_length=1)
    template_id: str = Field(..., min_length=1)
    channel: NotificationChannel
    variables: dict[str, str] | None = None
    priority_override: NotificationPriority | None = None


class NotificationResponse(BaseModel):
    notification_id: str
    subject: str
    body: str
    channel: str
    priority: str
    status: str


class NotificationSummary(BaseModel):
    total: int
    unread: int


_notification_center = NotificationCenter()


@router.post("/send", response_model=NotificationResponse)
async def send_notification(
    request: Request,
    body: SendNotificationRequest,
) -> NotificationResponse:
    """Send a notification using a template."""
    tenant_id = getattr(request.state, "tenant_id", "default")
    notif = _notification_center.send_notification(
        tenant_id=tenant_id,
        user_id=body.user_id,
        template_id=body.template_id,
        channel=body.channel,
        variables=body.variables,
        priority_override=body.priority_override,
    )
    return NotificationResponse(
        notification_id=notif.notification_id,
        subject=notif.subject,
        body=notif.body,
        channel=notif.channel.value,
        priority=notif.priority.value,
        status=notif.status.value,
    )


@router.get("/user/{user_id}", response_model=list[NotificationResponse])
async def get_user_notifications(
    request: Request,
    user_id: str,
    unread_only: bool = False,
) -> list[NotificationResponse]:
    """Get notifications for a user."""
    tenant_id = getattr(request.state, "tenant_id", "default")
    notifs = _notification_center.get_user_notifications(tenant_id, user_id, unread_only)
    return [
        NotificationResponse(
            notification_id=n.notification_id,
            subject=n.subject,
            body=n.body,
            channel=n.channel.value,
            priority=n.priority.value,
            status=n.status.value,
        )
        for n in notifs
    ]


@router.get("/user/{user_id}/summary", response_model=NotificationSummary)
async def get_notification_summary(
    request: Request,
    user_id: str,
) -> NotificationSummary:
    """Get unread notification count for a user."""
    tenant_id = getattr(request.state, "tenant_id", "default")
    total = len(_notification_center.get_user_notifications(tenant_id, user_id))
    unread = _notification_center.get_unread_count(tenant_id, user_id)
    return NotificationSummary(total=total, unread=unread)


@router.post("/{notification_id}/read")
async def mark_notification_read(notification_id: str) -> dict:
    """Mark a notification as read."""
    success = _notification_center.mark_read(notification_id)
    return {"notification_id": notification_id, "marked_read": success}
