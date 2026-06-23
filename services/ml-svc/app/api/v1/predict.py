from fastapi import APIRouter

from app.core.predictor import predict_duration
from app.core.trainer import train_duration_model
from pydantic import BaseModel

router = APIRouter(prefix="/predict", tags=["predict"])


class PredictDurationRequest(BaseModel):
    product_id: str
    work_center_id: str
    batch_size: float
    duration_planned_mins: float
    operator_skill_tags: list[str] | None = None
    historical_avg_ratio: float | None = None


class TrainRequest(BaseModel):
    historical_records: list[dict]


@router.post("/duration")
async def predict(req: PredictDurationRequest):
    result = predict_duration(
        product_id=req.product_id,
        work_center_id=req.work_center_id,
        batch_size=req.batch_size,
        duration_planned_mins=req.duration_planned_mins,
        operator_skill_tags=req.operator_skill_tags,
        historical_avg_ratio=req.historical_avg_ratio,
    )
    return {"success": True, "data": result, "error": None}


@router.post("/duration/train")
async def train(req: TrainRequest):
    result = train_duration_model(req.historical_records)
    return {"success": True, "data": result, "error": None}


@router.get("/duration")
async def predict_get(
    product_id: str,
    work_center_id: str,
    batch_size: float = 1.0,
    duration_planned_mins: float = 60.0,
):
    result = predict_duration(
        product_id=product_id,
        work_center_id=work_center_id,
        batch_size=batch_size,
        duration_planned_mins=duration_planned_mins,
    )
    return {"success": True, "data": result, "error": None}
