"""Feature Store for IPE ML models.

Provides centralized feature computation, caching, and serving for:
- pATP reliability features
- Feasibility scorer features
- Defect prediction features
- Supplier scoring features
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger("ipe.ml.feature_store")


@dataclass
class FeatureDefinition:
    name: str
    feature_type: str  # "computed", "cached", "realtime"
    entity_key: str  # e.g., "mo_id", "product_id", "supplier_id"
    description: str = ""
    ttl_seconds: int = 300
    dependencies: list[str] = field(default_factory=list)


@dataclass
class FeatureValue:
    feature_name: str
    entity_key: str
    entity_value: str
    value: Any
    computed_at: str = ""
    ttl_seconds: int = 300

    def __post_init__(self) -> None:
        if not self.computed_at:
            self.computed_at = datetime.now(UTC).isoformat()

    @property
    def is_expired(self) -> bool:
        from datetime import timedelta
        computed = datetime.fromisoformat(self.computed_at)
        return datetime.now(UTC) > computed + timedelta(seconds=self.ttl_seconds)


# IPE Feature Definitions
IPE_FEATURES: list[FeatureDefinition] = [
    # pATP Features
    FeatureDefinition("material_confidence", "computed", "mo_id", "Monte Carlo material availability confidence", 600, []),
    FeatureDefinition("supply_risk_score", "computed", "supplier_id", "Supplier risk score based on OTIF history", 3600, []),
    FeatureDefinition("lead_time_variability", "computed", "product_id", "Lead time coefficient of variation", 3600, []),
    FeatureDefinition("safety_stock_coverage", "computed", "product_id", "Safety stock coverage ratio", 600, []),

    # Feasibility Features
    FeatureDefinition("capacity_utilization", "realtime", "workcenter_id", "Current work center utilization %", 60, []),
    FeatureDefinition("labor_availability", "realtime", "workcenter_id", "Operator availability probability", 300, []),
    FeatureDefinition("demand_priority_score", "computed", "mo_id", "Multi-factor priority score", 300, ["customer_value", "margin", "urgency"]),
    FeatureDefinition("bom_completion_pct", "computed", "mo_id", "BOM component availability %", 600, ["material_confidence"]),

    # Quality Features
    FeatureDefinition("defect_rate_30d", "cached", "product_id", "30-day rolling defect rate", 3600, []),
    FeatureDefinition("spc_trend", "computed", "product_id", "SPC X-bar trend direction", 1800, []),
    FeatureDefinition("rework_probability", "computed", "mo_id", "Probability of rework based on quality history", 1800, ["defect_rate_30d"]),

    # Supplier Features
    FeatureDefinition("otif_score", "cached", "supplier_id", "On-time in-full delivery score", 86400, []),
    FeatureDefinition("quality_score", "cached", "supplier_id", "Quality acceptance rate", 86400, []),
    FeatureDefinition("cost_competitiveness", "computed", "supplier_id", "Price vs market benchmark", 86400, []),
    FeatureDefinition("risk_events_90d", "cached", "supplier_id", "Risk events in last 90 days", 3600, []),

    # Financial Features
    FeatureDefinition("margin_at_risk", "computed", "mo_id", "Revenue at risk from delays", 300, ["demand_priority_score"]),
    FeatureDefinition("cost_variance_pct", "computed", "mo_id", "Cost variance from plan %", 600, []),
    FeatureDefinition("energy_cost_per_unit", "computed", "mo_id", "Energy cost per production unit", 3600, []),
]


class FeatureStore:
    def __init__(self) -> None:
        self._features: dict[str, FeatureValue] = {}
        self._definitions: dict[str, FeatureDefinition] = {f.name: f for f in IPE_FEATURES}

    def get_feature(self, feature_name: str, entity_value: str) -> Any | None:
        key = f"{feature_name}:{entity_value}"
        fv = self._features.get(key)
        if fv and not fv.is_expired:
            return fv.value
        return None

    def set_feature(self, feature_name: str, entity_key: str, entity_value: str, value: Any) -> None:
        defn = self._definitions.get(feature_name)
        ttl = defn.ttl_seconds if defn else 300
        key = f"{feature_name}:{entity_value}"
        self._features[key] = FeatureValue(
            feature_name=feature_name,
            entity_key=entity_key,
            entity_value=entity_value,
            value=value,
            ttl_seconds=ttl,
        )

    def get_entity_features(self, entity_value: str) -> dict[str, Any]:
        result = {}
        for defn in IPE_FEATURES:
            val = self.get_feature(defn.name, entity_value)
            if val is not None:
                result[defn.name] = val
        return result

    def compute_material_features(self, mo_id: str, material_score: float, suppliers: list[dict]) -> dict[str, Any]:
        self.set_feature("material_confidence", "mo_id", mo_id, material_score)

        for supp in suppliers:
            sid = supp.get("supplier_id", "")
            if sid:
                self.set_feature("supply_risk_score", "supplier_id", sid, supp.get("risk_score", 0.5))
                self.set_feature("lead_time_variability", "product_id", sid, supp.get("lt_cv", 0.2))

        coverage = min(1.0, material_score * 1.1)
        self.set_feature("safety_stock_coverage", "product_id", mo_id, coverage)

        return self.get_entity_features(mo_id)

    def compute_feasibility_features(self, mo_id: str, capacity_util: float, labor_avail: float, priority: float) -> dict[str, Any]:
        self.set_feature("capacity_utilization", "workcenter_id", mo_id, capacity_util)
        self.set_feature("labor_availability", "workcenter_id", mo_id, labor_avail)
        self.set_feature("demand_priority_score", "mo_id", mo_id, priority)
        self.set_feature("bom_completion_pct", "mo_id", mo_id, min(100, capacity_util * 0.6 + labor_avail * 0.4))

        return self.get_entity_features(mo_id)

    def compute_quality_features(self, mo_id: str, product_id: str, defect_rate: float) -> dict[str, Any]:
        self.set_feature("defect_rate_30d", "product_id", product_id, defect_rate)
        self.set_feature("rework_probability", "mo_id", mo_id, defect_rate * 0.8)

        return self.get_entity_features(mo_id)

    def list_features(self) -> list[dict[str, Any]]:
        return [
            {
                "name": f.name,
                "type": f.feature_type,
                "entity": f.entity_key,
                "ttl": f.ttl_seconds,
                "dependencies": f.dependencies,
            }
            for f in IPE_FEATURES
        ]

    def get_expired_count(self) -> int:
        return sum(1 for fv in self._features.values() if fv.is_expired)


_feature_store: FeatureStore | None = None


def get_feature_store() -> FeatureStore:
    global _feature_store
    if _feature_store is None:
        _feature_store = FeatureStore()
    return _feature_store
