import random
from datetime import datetime, timedelta
from decimal import Decimal


def predict_delay(
    avg_delay_days: Decimal | None,
    delay_std_dev_days: Decimal | None,
    reliability_score: Decimal | None,
    distribution_type: str = "normal",
    distribution_params: dict | None = None,
    num_samples: int = 1000,
) -> dict:
    if avg_delay_days is None or delay_std_dev_days is None:
        return {
            "expected_delay_days": 0.0,
            "delay_std_dev": 0.0,
            "confidence": 0.0,
            "p10": 0.0,
            "p50": 0.0,
            "p90": 0.0,
        }
    mean = float(avg_delay_days)
    std = float(delay_std_dev_days) or 0.001
    reliability = float(reliability_score) if reliability_score else 0.5

    random.seed()
    samples: list[float] = []
    for _ in range(num_samples):
        if distribution_type == "lognormal":
            import math
            mu = math.log(mean**2 / math.sqrt(std**2 + mean**2))
            sigma = math.sqrt(math.log(1 + (std**2 / mean**2)))
            s = random.lognormvariate(mu, sigma)
        else:
            s = random.gauss(mean, std)
        samples.append(max(0.0, s))

    samples.sort()
    p10 = samples[int(num_samples * 0.1)]
    p50 = samples[int(num_samples * 0.5)]
    p90 = samples[int(num_samples * 0.9)]
    expected = sum(samples) / num_samples

    confidence = min(reliability * (1.0 - (std / (mean + 0.001))), 0.99)

    return {
        "expected_delay_days": round(expected, 2),
        "delay_std_dev": round(std, 2),
        "confidence": round(confidence, 4),
        "p10": round(p10, 2),
        "p50": round(p50, 2),
        "p90": round(p90, 2),
    }


def train_supplier_reliability_model(
    supplier_id: str,
    historical_delays: list[float],
    tracking_uri: str = "http://localhost:5000",
) -> dict:
    import mlflow

    with mlflow.start_run(run_name=f"supplier_reliability_{supplier_id}") as run:
        n = len(historical_delays)
        mu = sum(historical_delays) / n if n > 0 else 0.0
        variance = sum((d - mu) ** 2 for d in historical_delays) / n if n > 1 else 0.0
        sigma = variance ** 0.5

        mlflow.log_param("supplier_id", supplier_id)
        mlflow.log_param("sample_size", n)
        mlflow.log_metric("mu", round(mu, 4))
        mlflow.log_metric("sigma", round(sigma, 4))
        mlflow.log_metric("variance", round(variance, 4))

        mlflow.set_tag("model_type", "delay_distribution")
        mlflow.log_text(
            str({"mu": mu, "sigma": sigma, "distribution": "normal"}),
            "distribution_params.json",
        )

        return {
            "run_id": run.info.run_id,
            "mu": round(mu, 4),
            "sigma": round(sigma, 4),
            "sample_size": n,
        }


def adjust_expected_date(
    expected_date: datetime,
    avg_delay_days: Decimal | None,
    delay_std_dev_days: Decimal | None,
) -> dict:
    prediction = predict_delay(avg_delay_days, delay_std_dev_days, Decimal("0.0"))
    adjusted = expected_date + timedelta(days=prediction["expected_delay_days"])
    p90_date = expected_date + timedelta(days=prediction["p90"])
    return {
        "adjusted_date": adjusted.isoformat(),
        "p90_date": p90_date.isoformat(),
        "expected_delay_days": prediction["expected_delay_days"],
        "confidence": prediction["confidence"],
    }
