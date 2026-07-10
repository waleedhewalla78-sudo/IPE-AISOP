"""Sprint S3 — SES forecaster on cdm_demand_line (7/14/30d + MAPE)."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.core.forecaster import STANDARD_HORIZONS, forecast_series, mape, simple_exponential_smoothing
from app.core.forecaster_factory import forecast_with_factory, select_forecaster


@pytest.mark.parametrize("days", STANDARD_HORIZONS)
def test_forecast_series_standard_horizons(days: int):
    points = forecast_series([10.0, 12.0, 11.0, 13.0, 12.0], days)
    assert len(points) == days
    for point in points:
        assert point["lower"] <= point["value"] <= point["upper"]


def test_ses_factory_default():
    forecaster, version = select_forecaster([10.0] * 40, model="ses")
    assert version == "ses-v1"
    points, model = forecast_with_factory([10.0, 12.0, 11.0], 14, model="ses")
    assert model == "ses-v1"
    assert len(points) == 14


def test_mape_holdout():
    history = [100.0, 110.0, 105.0, 115.0, 108.0]
    predicted = [simple_exponential_smoothing(history[: i + 1]) for i in range(len(history))]
    score = mape(history[1:], predicted[1:])
    assert score is not None
    assert 0 <= score < 50


@pytest.mark.asyncio
async def test_forecast_api_horizon_days(client, auth_headers):
    product_id = str(uuid4())
    for days in (7, 14, 30):
        r = await client.get(
            f"/api/v1/demand/forecast?product_id={product_id}&days={days}",
            headers=auth_headers,
        )
        assert r.status_code == 200
        body = r.json()
        assert body["success"] is True
        assert body["data"]["horizon_days"] == days
        assert len(body["data"]["forecasts"]) == days
        assert body["data"]["source"] == "cdm_demand_line"


@pytest.mark.asyncio
async def test_accuracy_mape_endpoint(client, auth_headers):
    product_id = str(uuid4())
    r = await client.get(
        f"/api/v1/demand/accuracy?product_id={product_id}",
        headers=auth_headers,
    )
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert body["data"]["model"] == "ses"


@pytest.mark.asyncio
async def test_sense_cycle_14d(client, auth_headers):
    r = await client.post(
        "/api/v1/demand/sense",
        json={"days": 14, "horizon": "short"},
        headers=auth_headers,
    )
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["horizon_days"] == 14
    assert data["model"] == "ses"
