from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any


@dataclass
class GLMapping:
    gl_account: str
    cost_type: str
    description: str


@dataclass
class COGMBreakdown:
    material_cost: float
    labor_cost: float
    energy_cost: float
    overhead_cost: float
    total_cogm: float
    cogm_per_unit: float
    gl_accounts: dict[str, float] = field(default_factory=dict)


@dataclass
class COPQBreakdown:
    scrap_cost: float
    rework_cost: float
    inspection_cost: float
    warranty_cost: float
    total_copq: float
    copq_as_pct_of_revenue: float


@dataclass
class VarianceLine:
    cost_element: str
    planned: float
    actual: float
    variance: float
    variance_pct: float


@dataclass
class CostAccountingResult:
    product_id: str
    quantity: int
    selling_price: float
    revenue: float
    cogm: COGMBreakdown
    copq: COPQBreakdown
    gross_margin: float
    gross_margin_pct: float
    net_margin: float
    net_margin_pct: float
    variances: list[VarianceLine] = field(default_factory=list)
    xai_factors: dict[str, float] = field(default_factory=dict)


DEFAULT_GL_ACCOUNT_MAP: dict[str, str] = {
    "material": "5100-RAW-MATERIAL",
    "labor": "5200-DIRECT-LABOR",
    "energy": "5300-ENERGY",
    "overhead": "5400-MFG-OVERHEAD",
    "scrap": "6100-SCRAP",
    "rework": "6200-REWORK",
    "inspection": "6300-QUALITY-INSPECTION",
    "warranty": "6400-WARRANTY",
}


def get_gl_account_map(tenant_config: dict) -> dict:
    if tenant_config.get("gl_account_map"):
        merged = dict(DEFAULT_GL_ACCOUNT_MAP)
        merged.update(tenant_config["gl_account_map"])
        return merged
    return dict(DEFAULT_GL_ACCOUNT_MAP)


def compute_cogm(
    material_cost: float,
    labor_cost: float,
    energy_cost: float,
    overhead_cost: float,
    quantity: int,
    gl_account_map: dict[str, str] | None = None,
) -> COGMBreakdown:
    gl = gl_account_map or DEFAULT_GL_ACCOUNT_MAP
    total = material_cost + labor_cost + energy_cost + overhead_cost
    per_unit = total / quantity if quantity > 0 else 0.0

    gl_accounts = {
        gl["material"]: material_cost,
        gl["labor"]: labor_cost,
        gl["energy"]: energy_cost,
        gl["overhead"]: overhead_cost,
    }

    return COGMBreakdown(
        material_cost=round(material_cost, 2),
        labor_cost=round(labor_cost, 2),
        energy_cost=round(energy_cost, 2),
        overhead_cost=round(overhead_cost, 2),
        total_cogm=round(total, 2),
        cogm_per_unit=round(per_unit, 4),
        gl_accounts={k: round(v, 2) for k, v in gl_accounts.items()},
    )


def compute_copq(
    total_quantity: int,
    defect_rate_pct: float = 2.0,
    rework_rate_pct: float = 1.0,
    inspection_cost_per_unit: float = 5.0,
    warranty_cost_per_unit: float = 10.0,
    standard_cost_per_unit: float = 100.0,
    selling_price_per_unit: float = 150.0,
    gl_account_map: dict[str, str] | None = None,
) -> COPQBreakdown:
    _ = gl_account_map
    scrap_qty = total_quantity * (defect_rate_pct / 100.0)
    rework_qty = total_quantity * (rework_rate_pct / 100.0)

    scrap_cost = scrap_qty * standard_cost_per_unit
    rework_cost = rework_qty * standard_cost_per_unit * 0.3
    inspection_cost = total_quantity * inspection_cost_per_unit
    warranty_cost = total_quantity * warranty_cost_per_unit * 0.05

    total_copq = scrap_cost + rework_cost + inspection_cost + warranty_cost
    revenue = total_quantity * selling_price_per_unit
    copq_pct = (total_copq / revenue * 100.0) if revenue > 0 else 0.0

    return COPQBreakdown(
        scrap_cost=round(scrap_cost, 2),
        rework_cost=round(rework_cost, 2),
        inspection_cost=round(inspection_cost, 2),
        warranty_cost=round(warranty_cost, 2),
        total_copq=round(total_copq, 2),
        copq_as_pct_of_revenue=round(copq_pct, 2),
    )


def compute_variance_analysis(
    planned: dict[str, float],
    actual: dict[str, float],
    gl_account_map: dict[str, str] | None = None,
) -> list[VarianceLine]:
    _ = gl_account_map
    variances: list[VarianceLine] = []
    all_elements = set(list(planned.keys()) + list(actual.keys()))

    for element in all_elements:
        p = planned.get(element, 0.0)
        a = actual.get(element, 0.0)
        var = a - p
        var_pct = (var / p * 100.0) if p > 0 else 0.0

        variances.append(VarianceLine(
            cost_element=element,
            planned=round(p, 2),
            actual=round(a, 2),
            variance=round(var, 2),
            variance_pct=round(var_pct, 2),
        ))

    return variances


def compute_cost_accounting(
    product_id: str,
    quantity: int,
    selling_price: float,
    material_cost: float,
    labor_cost: float,
    energy_cost: float,
    overhead_cost: float,
    actual_costs: dict[str, float] | None = None,
    defect_rate_pct: float = 2.0,
    rework_rate_pct: float = 1.0,
    inspection_cost_per_unit: float = 5.0,
    warranty_cost_per_unit: float = 10.0,
    gl_account_map: dict[str, str] | None = None,
) -> CostAccountingResult:
    cogm = compute_cogm(
        material_cost, labor_cost, energy_cost, overhead_cost, quantity,
        gl_account_map=gl_account_map,
    )
    copq = compute_copq(
        quantity, defect_rate_pct, rework_rate_pct,
        inspection_cost_per_unit, warranty_cost_per_unit,
        standard_cost_per_unit=cogm.cogm_per_unit,
        selling_price_per_unit=selling_price,
        gl_account_map=gl_account_map,
    )

    revenue = selling_price * quantity
    total_cost = cogm.total_cogm + copq.total_copq
    gross_margin = revenue - cogm.total_cogm
    gross_margin_pct = (gross_margin / revenue * 100.0) if revenue > 0 else 0.0
    net_margin = revenue - total_cost
    net_margin_pct = (net_margin / revenue * 100.0) if revenue > 0 else 0.0

    variances: list[VarianceLine] = []
    if actual_costs:
        planned_costs = {
            "material": material_cost,
            "labor": labor_cost,
            "energy": energy_cost,
            "overhead": overhead_cost,
        }
        variances = compute_variance_analysis(
            planned_costs, actual_costs,
            gl_account_map=gl_account_map,
        )

    xai_factors = {
        "cogm_weight": round(cogm.total_cogm / max(1, total_cost), 4),
        "copq_weight": round(copq.total_copq / max(1, total_cost), 4),
        "margin_health": round(min(1.0, max(0.0, gross_margin_pct / 100.0)), 4),
    }

    return CostAccountingResult(
        product_id=product_id,
        quantity=quantity,
        selling_price=selling_price,
        revenue=round(revenue, 2),
        cogm=cogm,
        copq=copq,
        gross_margin=round(gross_margin, 2),
        gross_margin_pct=round(gross_margin_pct, 2),
        net_margin=round(net_margin, 2),
        net_margin_pct=round(net_margin_pct, 2),
        variances=variances,
        xai_factors=xai_factors,
    )