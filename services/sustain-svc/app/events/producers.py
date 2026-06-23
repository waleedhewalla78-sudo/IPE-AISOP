from __future__ import annotations

import logging
from datetime import UTC, datetime
from uuid import uuid4

from ipe_shared.events.producer import kafka_producer

logger = logging.getLogger(__name__)


async def emit_circularity_scored(
    tenant_id: str,
    product_id: str,
    circularity_score: float,
    material_recovery_pct: float,
    take_back_eligible: bool,
) -> None:
    payload = {
        "product_id": product_id,
        "circularity_score": circularity_score,
        "material_recovery_pct": material_recovery_pct,
        "take_back_eligible": take_back_eligible,
    }
    envelope = kafka_producer.build_envelope(
        event_type="circularity_scored",
        tenant_id=tenant_id,
        payload=payload,
    )
    await kafka_producer.send_event("sustainability", "circularity_scored", key=product_id, value=envelope)
    logger.info("Emitted ipe.sustainability.circularity_scored for product %s (score=%.2f)", product_id, circularity_score)


async def emit_eol_planned(
    tenant_id: str,
    product_id: str,
    eol_risk_score: float,
    recommended_action: str,
    phase_out_date: str | None = None,
) -> None:
    payload = {
        "product_id": product_id,
        "eol_risk_score": eol_risk_score,
        "recommended_action": recommended_action,
        "phase_out_date": phase_out_date,
    }
    envelope = kafka_producer.build_envelope(
        event_type="eol_planned",
        tenant_id=tenant_id,
        payload=payload,
    )
    await kafka_producer.send_event("sustainability", "eol_planned", key=product_id, value=envelope)
    logger.info("Emitted ipe.sustainability.eol_planned for product %s (risk=%.2f)", product_id, eol_risk_score)