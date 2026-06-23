from __future__ import annotations
import json
from dataclasses import dataclass, field
from typing import Any

from ipe_shared.config import settings


@dataclass
class SlackMessage:
    channel: str
    text: str
    blocks: list[dict[str, Any]] = field(default_factory=list)


def format_disruption_alert(
    disruption_type: str,
    source_id: str,
    source_name: str,
    delay_days: float,
    impacted_mo_count: int,
    total_cost_impact: float,
    severity: str = "high",
) -> SlackMessage:
    severity_emoji = {"critical": ":rotating_light:", "high": ":warning:", "medium": ":large_yellow_circle:", "low": ":white_circle:"}
    emoji = severity_emoji.get(severity, ":warning:")

    blocks = [
        {"type": "header", "text": {"type": "plain_text", "text": f"{emoji} Supply Chain Disruption Alert"}},
        {"type": "section", "fields": [
            {"type": "mrkdwn", "text": f"*Type:*\n{disruption_type.replace('_', ' ').title()}"},
            {"type": "mrkdwn", "text": f"*Source:*\n{source_name} ({source_id})"},
            {"type": "mrkdwn", "text": f"*Delay:*\n{delay_days:.0f} days"},
            {"type": "mrkdwn", "text": f"*Severity:*\n{severity.upper()}"},
        ]},
        {"type": "section", "fields": [
            {"type": "mrkdwn", "text": f"*Impacted MOs:*\n{impacted_mo_count}"},
            {"type": "mrkdwn", "text": f"*Revenue at Risk:*\n${total_cost_impact:,.0f}"},
        ]},
        {"type": "actions", "elements": [
            {"type": "button", "text": {"type": "plain_text", "text": "Open War Room"}, "url": "/war-room", "style": "danger"},
            {"type": "button", "text": {"type": "plain_text", "text": "Assign Mitigation"}, "url": "/war-room/mitigate", "style": "primary"},
        ]},
    ]

    return SlackMessage(
        channel=getattr(settings, "SLACK_CHANNEL", "#ipe-war-room"),
        text=f"{emoji} {disruption_type} disruption at {source_name}: {delay_days:.0f}d delay, {impacted_mo_count} MOs impacted, ${total_cost_impact:,.0f} at risk",
        blocks=blocks,
    )


def format_teams_alert(
    disruption_type: str,
    source_id: str,
    source_name: str,
    delay_days: float,
    impacted_mo_count: int,
    total_cost_impact: float,
) -> dict[str, Any]:
    return {
        "@type": "MessageCard",
        "@context": "http://schema.org/extensions",
        "themeColor": "FF0000" if delay_days > 14 else "FFA500",
        "summary": f"IPE Disruption: {disruption_type}",
        "sections": [{
            "activityTitle": f"Supply Chain Disruption: {disruption_type.replace('_', ' ').title()}",
            "facts": [
                {"name": "Source", "value": f"{source_name} ({source_id})"},
                {"name": "Delay", "value": f"{delay_days:.0f} days"},
                {"name": "Impacted MOs", "value": str(impacted_mo_count)},
                {"name": "Revenue at Risk", "value": f"${total_cost_impact:,.0f}"},
            ],
            "markdown": True,
        }],
        "potentialAction": [
            {"@type": "OpenUri", "name": "Open War Room", "targets": [{"uri": "/war-room"}]},
        ],
    }


async def send_slack_alert(message: SlackMessage) -> bool:
    webhook_url = getattr(settings, "SLACK_WEBHOOK_URL", "")
    if not webhook_url:
        return False

    payload = {
        "channel": message.channel,
        "text": message.text,
        "blocks": message.blocks,
    }

    try:
        import httpx
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(webhook_url, json=payload)
            return resp.status_code == 200
    except Exception:
        return False


async def send_teams_alert(card: dict[str, Any]) -> bool:
    webhook_url = getattr(settings, "TEAMS_WEBHOOK_URL", "")
    if not webhook_url:
        return False

    try:
        import httpx
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(webhook_url, json=card)
            return resp.status_code == 200
    except Exception:
        return False