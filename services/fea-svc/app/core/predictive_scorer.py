"""Predictive risk scoring — projects feasibility gates to T+3/7/14."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.scorer import calculate_feasibility, score_from_mo


def _score_to_color(score: float) -> str:
    if score >= 80:
        return "green"
    if score >= 50:
        return "amber"
    return "red"


def _calculate_trend(current: float, predictions: dict[int, dict[str, Any]]) -> str:
    scores = [current] + [predictions[h]["predicted_score"] for h in sorted(predictions)]
    if len(scores) < 2:
        return "stable"
    deltas = [scores[i + 1] - scores[i] for i in range(len(scores) - 1)]
    if any(s < 50 for s in scores[1:]) and scores[0] >= 70:
        return "crisis_approaching"
    if all(d <= -5 for d in deltas):
        return "deteriorating"
    if all(d >= 5 for d in deltas):
        return "improving"
    return "stable"


@dataclass
class PredictiveRiskScorer:
    """Calculates feasibility scores at T+3, T+7, T+14 by projecting trends."""

    async def score_future(
        self,
        db: AsyncSession | None,
        tenant_id: str,
        mo_id: str,
        horizons: list[int] | None = None,
    ) -> dict[str, Any]:
        horizons = horizons or [3, 7, 14]
        if db is not None:
            current = await score_from_mo(tenant_id, mo_id, session=db)
        else:
            current = calculate_feasibility(
                demand_score=90,
                bom_score=100,
                material_score=85,
                capacity_score=80,
                labor_score=90,
            )

        current_score = float(current.get("feasibility_score") or current.get("score") or 0)
        gates = current.get("gate_scores") or {}
        predictions: dict[int, dict[str, Any]] = {}

        for days in horizons:
            material = max(0.0, float(gates.get("material", 85)) - days * 3.5)
            capacity = max(0.0, float(gates.get("capacity", 80)) - days * 2.0)
            delivery = max(0.0, float(gates.get("delivery", gates.get("labor", 90))) - days * 1.5)
            future = calculate_feasibility(
                demand_score=float(gates.get("demand", 90)),
                bom_score=float(gates.get("bom", 100)),
                material_score=material,
                capacity_score=capacity,
                labor_score=delivery,
            )
            comp = float(future["feasibility_score"])
            weakest = future.get("primary_constraint") or "material"
            predictions[days] = {
                "horizon_days": days,
                "predicted_score": round(comp, 2),
                "predicted_color": _score_to_color(comp),
                "gates": future.get("gate_scores"),
                "primary_risk": weakest,
                "risk_driver": f"{weakest} projected to degrade over {days} days",
                "score": round(comp, 2),
                "color": _score_to_color(comp),
            }

        if db is not None:
            await self._store_predictions(db, tenant_id, mo_id, predictions)

        trend = _calculate_trend(current_score, predictions)
        earliest = None
        for days in sorted(predictions):
            if predictions[days]["predicted_color"] in ("amber", "red"):
                earliest = (date.today() + timedelta(days=days)).isoformat()
                break

        return {
            "mo_id": mo_id,
            "current": {
                "score": round(current_score, 2),
                "color": _score_to_color(current_score),
                "gates": gates,
            },
            "predictions": predictions,
            "trend": trend,
            "earliest_risk_date": earliest,
            "recommended_action": (
                "Act within 2 days to prevent material gate failure"
                if trend == "crisis_approaching"
                else "Monitor — no immediate crisis predicted"
            ),
        }

    async def _store_predictions(
        self,
        db: AsyncSession,
        tenant_id: str,
        mo_id: str,
        predictions: dict[int, dict[str, Any]],
    ) -> None:
        today = date.today()
        for days, pred in predictions.items():
            await db.execute(
                text("""
                    INSERT INTO cdm_prediction_log (
                        tenant_id, mo_id, prediction_date, horizon_days, target_date,
                        predicted_score, predicted_color, primary_risk_gate, risk_explanation
                    ) VALUES (
                        :tenant_id, :mo_id, :prediction_date, :horizon_days, :target_date,
                        :predicted_score, :predicted_color, :primary_risk_gate, :risk_explanation
                    )
                """),
                {
                    "tenant_id": UUID(tenant_id),
                    "mo_id": UUID(mo_id) if _is_uuid(mo_id) else UUID(int=0),
                    "prediction_date": today,
                    "horizon_days": days,
                    "target_date": today + timedelta(days=days),
                    "predicted_score": pred["predicted_score"],
                    "predicted_color": pred["predicted_color"],
                    "primary_risk_gate": pred["primary_risk"],
                    "risk_explanation": pred["risk_driver"],
                },
            )


def _is_uuid(value: str) -> bool:
    try:
        UUID(value)
        return True
    except ValueError:
        return False
