"""ABC/XYZ product segmentation for planning intelligence."""
from __future__ import annotations

import math
from collections import defaultdict
from datetime import UTC, date, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ipe_shared.models.demand import DemandLine
from ipe_shared.models.planning_intelligence import ProductSegment, SegmentationConfig
from ipe_shared.models.product import Product


DEFAULT_SEGMENTATION_CONFIG = {
    "abc_a_threshold_pct": 80.0,
    "abc_b_threshold_pct": 95.0,
    "xyz_x_threshold": 0.5,
    "xyz_y_threshold": 1.0,
    "service_level_ax": 99.0,
    "service_level_ay": 97.0,
    "service_level_az": 95.0,
    "service_level_bx": 97.0,
    "service_level_by": 95.0,
    "service_level_bz": 90.0,
    "service_level_cx": 95.0,
    "service_level_cy": 90.0,
    "service_level_cz": 85.0,
    "history_months": 12,
}

FORECAST_MODEL_RECOMMENDATIONS = {
    "X": "statistical_baseline",
    "Y": "seasonal_ml_hybrid",
    "Z": "event_driven_manual_review",
}

REVIEW_FREQUENCY = {"A": "weekly", "B": "biweekly", "C": "monthly"}


def classify_abc(
    products_with_revenue: list[dict],
    a_threshold: float,
    b_threshold: float,
) -> list[dict]:
    """Classify products by cumulative revenue contribution."""
    sorted_products = sorted(
        products_with_revenue,
        key=lambda item: float(item.get("revenue_total") or item.get("revenue") or 0),
        reverse=True,
    )
    total_revenue = sum(
        max(0.0, float(item.get("revenue_total") or item.get("revenue") or 0))
        for item in sorted_products
    )
    if total_revenue <= 0:
        return [
            {
                **item,
                "revenue_total": float(item.get("revenue_total") or item.get("revenue") or 0),
                "revenue_share_pct": 0.0,
                "cumulative_revenue_pct": 0.0,
                "abc_class": "C",
            }
            for item in sorted_products
        ]

    cumulative = 0.0
    classified = []
    for item in sorted_products:
        revenue = max(0.0, float(item.get("revenue_total") or item.get("revenue") or 0))
        share_pct = revenue / total_revenue * 100
        cumulative += share_pct
        if cumulative <= a_threshold:
            abc_class = "A"
        elif cumulative <= b_threshold:
            abc_class = "B"
        else:
            abc_class = "C"

        classified.append(
            {
                **item,
                "revenue_total": revenue,
                "revenue_share_pct": share_pct,
                "cumulative_revenue_pct": cumulative,
                "abc_class": abc_class,
            }
        )
    return classified


def classify_xyz(cv: float | None, x_threshold: float, y_threshold: float) -> str:
    """Classify demand variability by coefficient of variation."""
    if cv is None or math.isnan(cv) or math.isinf(cv):
        return "Z"
    if cv <= x_threshold:
        return "X"
    if cv <= y_threshold:
        return "Y"
    return "Z"


def calculate_demand_profile(
    weekly_quantities: list[float],
    x_threshold: float,
    y_threshold: float,
) -> dict[str, float | str]:
    """Return demand statistics and XYZ class for weekly demand buckets."""
    if not weekly_quantities or sum(weekly_quantities) <= 0:
        return {
            "demand_mean": 0.0,
            "demand_stddev": 0.0,
            "demand_cv": math.inf,
            "xyz_class": "Z",
        }

    mean = sum(weekly_quantities) / len(weekly_quantities)
    if len(weekly_quantities) > 1:
        variance = sum((qty - mean) ** 2 for qty in weekly_quantities) / (
            len(weekly_quantities) - 1
        )
        stddev = math.sqrt(variance)
    else:
        stddev = 0.0
    cv = stddev / mean if mean else math.inf
    return {
        "demand_mean": mean,
        "demand_stddev": stddev,
        "demand_cv": cv,
        "xyz_class": classify_xyz(cv, x_threshold, y_threshold),
    }


def get_segment_policy(
    abc_class: str,
    xyz_class: str,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Map an ABC/XYZ combination to replenishment policy metadata."""
    cfg = {**DEFAULT_SEGMENTATION_CONFIG, **(config or {})}
    segment = f"{abc_class}{xyz_class}".lower()
    service_level = float(cfg.get(f"service_level_{segment}", 95.0))
    return {
        "combined_segment": f"{abc_class}{xyz_class}",
        "target_service_level_pct": service_level,
        "forecast_model_recommendation": FORECAST_MODEL_RECOMMENDATIONS.get(
            xyz_class,
            "statistical_baseline",
        ),
        "review_frequency": REVIEW_FREQUENCY.get(abc_class, "monthly"),
    }


def _config_to_dict(config: SegmentationConfig | None) -> dict[str, Any]:
    values = DEFAULT_SEGMENTATION_CONFIG.copy()
    if config is None:
        return values
    for key in values:
        value = getattr(config, key, None)
        if value is not None:
            values[key] = float(value) if key != "history_months" else int(value)
    return values


def _line_revenue(line: DemandLine, product: Product) -> float:
    quantity = float(line.quantity or 0)
    explicit_revenue = getattr(line, "revenue", None)
    if explicit_revenue is not None:
        return float(explicit_revenue or 0)

    margin = getattr(line, "margin", None)
    if margin is not None:
        return quantity * float(margin or 0)

    margin_pct = getattr(line, "margin_pct", None)
    if margin_pct is not None:
        return quantity * float(margin_pct or 0)

    for price_attr in ("list_price", "unit_price"):
        value = getattr(product, price_attr, None)
        if value is not None:
            return quantity * float(value or 0)

    return quantity


class SegmentationEngine:
    """Runs tenant-scoped ABC/XYZ segmentation and persists ProductSegment rows."""

    async def get_config(self, db: AsyncSession, tenant_id: UUID) -> dict[str, Any]:
        result = await db.execute(
            select(SegmentationConfig).where(SegmentationConfig.tenant_id == tenant_id)
        )
        config = result.scalar_one_or_none()
        if config is None:
            config = SegmentationConfig(tenant_id=tenant_id)
            db.add(config)
            await db.flush()
        return _config_to_dict(config)

    async def update_config(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        updates: dict[str, Any],
    ) -> dict[str, Any]:
        result = await db.execute(
            select(SegmentationConfig).where(SegmentationConfig.tenant_id == tenant_id)
        )
        config = result.scalar_one_or_none()
        if config is None:
            config = SegmentationConfig(tenant_id=tenant_id)
            db.add(config)

        for key, value in updates.items():
            if value is not None and key in DEFAULT_SEGMENTATION_CONFIG:
                setattr(config, key, value)
        await db.commit()
        await db.refresh(config)
        return _config_to_dict(config)

    async def run_segmentation(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        config_overrides: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        config = await self.get_config(db, tenant_id)
        if config_overrides:
            config.update({k: v for k, v in config_overrides.items() if v is not None})

        products = (
            await db.execute(select(Product).where(Product.tenant_id == tenant_id))
        ).scalars().all()
        product_map = {product.id: product for product in products}
        cutoff = datetime.now(UTC) - timedelta(days=int(config["history_months"]) * 30)
        demand_lines = (
            await db.execute(
                select(DemandLine)
                .where(DemandLine.tenant_id == tenant_id)
                .where(DemandLine.required_date >= cutoff)
            )
        ).scalars().all()

        revenue_by_product: dict[UUID, float] = defaultdict(float)
        weekly_demand: dict[UUID, dict[tuple[int, int], float]] = defaultdict(
            lambda: defaultdict(float)
        )
        for line in demand_lines:
            product = product_map.get(line.product_id)
            if product is None:
                continue
            revenue_by_product[line.product_id] += _line_revenue(line, product)
            required_date = line.required_date.date()
            iso_year, iso_week, _ = required_date.isocalendar()
            weekly_demand[line.product_id][(iso_year, iso_week)] += float(line.quantity or 0)

        abc_input = [
            {
                "product_id": product.id,
                "product_name": product.name,
                "internal_ref": product.internal_ref,
                "revenue_total": revenue_by_product.get(product.id, 0.0),
            }
            for product in products
        ]
        abc_rows = classify_abc(
            abc_input,
            float(config["abc_a_threshold_pct"]),
            float(config["abc_b_threshold_pct"]),
        )

        segmentation_date = date.today()
        items = []
        class_counts = {"A": 0, "B": 0, "C": 0, "X": 0, "Y": 0, "Z": 0}
        for abc_row in abc_rows:
            product_id = abc_row["product_id"]
            profile = calculate_demand_profile(
                list(weekly_demand.get(product_id, {}).values()),
                float(config["xyz_x_threshold"]),
                float(config["xyz_y_threshold"]),
            )
            xyz_class = str(profile["xyz_class"])
            abc_class = str(abc_row["abc_class"])
            policy = get_segment_policy(abc_class, xyz_class, config)
            class_counts[abc_class] += 1
            class_counts[xyz_class] += 1

            result = await db.execute(
                select(ProductSegment).where(
                    ProductSegment.tenant_id == tenant_id,
                    ProductSegment.product_id == product_id,
                    ProductSegment.segmentation_date == segmentation_date,
                )
            )
            segment = result.scalar_one_or_none()
            if segment is None:
                segment = ProductSegment(
                    tenant_id=tenant_id,
                    product_id=product_id,
                    segmentation_date=segmentation_date,
                )
                db.add(segment)

            segment.abc_class = abc_class
            segment.revenue_total = abc_row["revenue_total"]
            segment.revenue_share_pct = abc_row["revenue_share_pct"]
            segment.cumulative_revenue_pct = abc_row["cumulative_revenue_pct"]
            segment.xyz_class = xyz_class
            segment.demand_cv = (
                None if math.isinf(float(profile["demand_cv"])) else profile["demand_cv"]
            )
            segment.demand_mean = profile["demand_mean"]
            segment.demand_stddev = profile["demand_stddev"]
            segment.combined_segment = policy["combined_segment"]
            segment.target_service_level_pct = policy["target_service_level_pct"]
            segment.forecast_model_recommendation = policy["forecast_model_recommendation"]
            segment.review_frequency = policy["review_frequency"]

            items.append(
                {
                    "product_id": str(product_id),
                    "product_name": abc_row["product_name"],
                    "internal_ref": abc_row["internal_ref"],
                    "abc_class": abc_class,
                    "xyz_class": xyz_class,
                    **policy,
                    "revenue_total": round(float(abc_row["revenue_total"]), 2),
                    "revenue_share_pct": round(float(abc_row["revenue_share_pct"]), 4),
                    "cumulative_revenue_pct": round(float(abc_row["cumulative_revenue_pct"]), 4),
                    "demand_mean": round(float(profile["demand_mean"]), 4),
                    "demand_stddev": round(float(profile["demand_stddev"]), 4),
                    "demand_cv": None
                    if math.isinf(float(profile["demand_cv"]))
                    else round(float(profile["demand_cv"]), 4),
                }
            )

        await db.commit()
        return {
            "segmentation_date": segmentation_date.isoformat(),
            "total_products": len(items),
            "class_counts": class_counts,
            "items": items,
        }
