from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from uuid import uuid4


class RFQState(StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"
    RESPONDING = "responding"
    UNDER_REVIEW = "under_review"
    AWARDED = "awarded"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


VALID_TRANSITIONS: dict[RFQState, set[RFQState]] = {
    RFQState.DRAFT: {RFQState.PUBLISHED, RFQState.CANCELLED},
    RFQState.PUBLISHED: {RFQState.RESPONDING, RFQState.CANCELLED, RFQState.EXPIRED},
    RFQState.RESPONDING: {RFQState.UNDER_REVIEW, RFQState.CANCELLED},
    RFQState.UNDER_REVIEW: {RFQState.AWARDED, RFQState.CANCELLED},
    RFQState.AWARDED: set(),
    RFQState.CANCELLED: set(),
    RFQState.EXPIRED: set(),
}

_rfq_store: dict[str, dict] = {}
_rfq_response_store: dict[str, list[dict]] = {}


def create_rfq(tenant_id: str, data: dict) -> dict:
    rfq_id = str(uuid4())
    now = datetime.now(UTC).isoformat()
    rfq = {
        "rfq_id": rfq_id,
        "tenant_id": tenant_id,
        "title": data.get("title", ""),
        "description": data.get("description", ""),
        "items": data.get("items", []),
        "requirements": data.get("requirements", {}),
        "deadline": data.get("deadline"),
        "state": RFQState.DRAFT,
        "created_at": now,
        "updated_at": now,
    }
    _rfq_store[rfq_id] = rfq
    _rfq_response_store[rfq_id] = []
    return rfq


def _validate_transition(current: RFQState, target: RFQState) -> None:
    if target not in VALID_TRANSITIONS.get(current, set()):
        raise ValueError(f"Invalid transition: {current} -> {target}")


def publish_rfq(rfq_id: str) -> dict:
    rfq = _rfq_store.get(rfq_id)
    if not rfq:
        raise ValueError(f"RFQ {rfq_id} not found")
    _validate_transition(RFQState(rfq["state"]), RFQState.PUBLISHED)
    rfq["state"] = RFQState.PUBLISHED
    rfq["updated_at"] = datetime.now(UTC).isoformat()
    return rfq


def respond_to_rfq(rfq_id: str, supplier_id: str, response_data: dict) -> dict:
    rfq = _rfq_store.get(rfq_id)
    if not rfq:
        raise ValueError(f"RFQ {rfq_id} not found")
    current_state = RFQState(rfq["state"])
    if current_state not in {RFQState.PUBLISHED, RFQState.RESPONDING}:
        raise ValueError(f"RFQ is in state {current_state}, cannot accept responses")
    if current_state == RFQState.PUBLISHED:
        rfq["state"] = RFQState.RESPONDING
        rfq["updated_at"] = datetime.now(UTC).isoformat()
    response = {
        "response_id": str(uuid4()),
        "rfq_id": rfq_id,
        "supplier_id": supplier_id,
        "price": response_data.get("price", 0.0),
        "lead_time_days": response_data.get("lead_time_days", 0),
        "terms": response_data.get("terms", {}),
        "notes": response_data.get("notes", ""),
        "submitted_at": datetime.now(UTC).isoformat(),
    }
    _rfq_response_store[rfq_id].append(response)
    return response


def evaluate_rfq(rfq_id: str) -> dict:
    rfq = _rfq_store.get(rfq_id)
    if not rfq:
        raise ValueError(f"RFQ {rfq_id} not found")
    current_state = RFQState(rfq["state"])
    _validate_transition(current_state, RFQState.UNDER_REVIEW)
    responses = _rfq_response_store.get(rfq_id, [])
    evaluations = []
    for resp in responses:
        price_score = max(0, 100 - resp.get("price", 0) * 0.5)
        lead_time_score = max(0, 100 - resp.get("lead_time_days", 0) * 2)
        composite = round(price_score * 0.6 + lead_time_score * 0.4, 2)
        evaluations.append({
            "response_id": resp["response_id"],
            "supplier_id": resp["supplier_id"],
            "price": resp.get("price", 0.0),
            "lead_time_days": resp.get("lead_time_days", 0),
            "price_score": round(price_score, 2),
            "lead_time_score": round(lead_time_score, 2),
            "composite_score": composite,
        })
    evaluations.sort(key=lambda e: e["composite_score"], reverse=True)
    rfq["state"] = RFQState.UNDER_REVIEW
    rfq["updated_at"] = datetime.now(UTC).isoformat()
    return {
        "rfq_id": rfq_id,
        "state": rfq["state"],
        "response_count": len(responses),
        "evaluations": evaluations,
    }


def award_rfq(rfq_id: str, winning_supplier_id: str) -> dict:
    rfq = _rfq_store.get(rfq_id)
    if not rfq:
        raise ValueError(f"RFQ {rfq_id} not found")
    _validate_transition(RFQState(rfq["state"]), RFQState.AWARDED)
    responses = _rfq_response_store.get(rfq_id, [])
    winning = None
    for resp in responses:
        if resp["supplier_id"] == winning_supplier_id:
            winning = resp
            break
    rfq["state"] = RFQState.AWARDED
    rfq["awarded_supplier_id"] = winning_supplier_id
    rfq["updated_at"] = datetime.now(UTC).isoformat()
    return {
        "rfq_id": rfq_id,
        "state": RFQState.AWARDED,
        "awarded_supplier_id": winning_supplier_id,
        "winning_response": winning,
    }


def cancel_rfq(rfq_id: str) -> dict:
    rfq = _rfq_store.get(rfq_id)
    if not rfq:
        raise ValueError(f"RFQ {rfq_id} not found")
    _validate_transition(RFQState(rfq["state"]), RFQState.CANCELLED)
    rfq["state"] = RFQState.CANCELLED
    rfq["updated_at"] = datetime.now(UTC).isoformat()
    return {
        "rfq_id": rfq_id,
        "state": RFQState.CANCELLED,
    }