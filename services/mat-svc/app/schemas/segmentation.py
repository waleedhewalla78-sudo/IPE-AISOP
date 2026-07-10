"""Pydantic schemas for ABC/XYZ segmentation APIs."""
from __future__ import annotations

from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SegmentationConfigBase(BaseModel):
    abc_a_threshold_pct: float | None = Field(default=None, gt=0, le=100)
    abc_b_threshold_pct: float | None = Field(default=None, gt=0, le=100)
    xyz_x_threshold: float | None = Field(default=None, ge=0)
    xyz_y_threshold: float | None = Field(default=None, ge=0)
    service_level_ax: float | None = Field(default=None, gt=0, le=100)
    service_level_ay: float | None = Field(default=None, gt=0, le=100)
    service_level_az: float | None = Field(default=None, gt=0, le=100)
    service_level_bx: float | None = Field(default=None, gt=0, le=100)
    service_level_by: float | None = Field(default=None, gt=0, le=100)
    service_level_bz: float | None = Field(default=None, gt=0, le=100)
    service_level_cx: float | None = Field(default=None, gt=0, le=100)
    service_level_cy: float | None = Field(default=None, gt=0, le=100)
    service_level_cz: float | None = Field(default=None, gt=0, le=100)
    history_months: int | None = Field(default=None, ge=1, le=60)


class SegmentationRunRequest(BaseModel):
    config_overrides: SegmentationConfigBase | None = None


class SegmentationConfigUpdate(SegmentationConfigBase):
    pass


class SegmentationConfigResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    abc_a_threshold_pct: float
    abc_b_threshold_pct: float
    xyz_x_threshold: float
    xyz_y_threshold: float
    service_level_ax: float
    service_level_ay: float
    service_level_az: float
    service_level_bx: float
    service_level_by: float
    service_level_bz: float
    service_level_cx: float
    service_level_cy: float
    service_level_cz: float
    history_months: int


class SegmentationResultItem(BaseModel):
    product_id: UUID | str
    product_name: str | None = None
    internal_ref: str | None = None
    segmentation_date: date | str | None = None
    abc_class: str
    xyz_class: str
    combined_segment: str
    target_service_level_pct: float | None = None
    forecast_model_recommendation: str | None = None
    review_frequency: str | None = None
    revenue_total: float | None = None
    revenue_share_pct: float | None = None
    cumulative_revenue_pct: float | None = None
    demand_mean: float | None = None
    demand_stddev: float | None = None
    demand_cv: float | None = None


class SegmentationRunResponse(BaseModel):
    segmentation_date: date | str
    total_products: int
    class_counts: dict[str, int]
    items: list[SegmentationResultItem]
