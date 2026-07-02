"""Outcomes API — alias for analytics endpoints (Kong /api/v1/outcomes, Release 2)."""

from fastapi import APIRouter

from app.api.v1.analytics import capture_otd_baseline, get_otd_baseline, roi_metrics

router = APIRouter(prefix="/outcomes", tags=["outcomes"])

router.add_api_route("/otd-baseline", get_otd_baseline, methods=["GET"])
router.add_api_route("/otd-baseline/capture", capture_otd_baseline, methods=["POST"])
router.add_api_route("/roi-metrics", roi_metrics, methods=["GET"])
