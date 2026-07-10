from __future__ import annotations

FIELDS = ("consensus_qty", "consensus_revenue", "consensus_cost", "consensus_profit")


def _get_value(row: object, field: str) -> float:
    if isinstance(row, dict):
        value = row.get(field)
    else:
        value = getattr(row, field, None)
    return float(value or 0)


def totals(rows: list[object]) -> dict[str, float]:
    return {field: sum(_get_value(row, field) for row in rows) for field in FIELDS}


def compare_totals(base_rows: list[object], compare_rows: list[object]) -> dict:
    base = totals(base_rows)
    compare = totals(compare_rows)
    delta = {field: compare[field] - base[field] for field in FIELDS}
    delta_pct = {
        field: (delta[field] / base[field] * 100.0) if base[field] else 0.0
        for field in FIELDS
    }
    return {"base": base, "compare": compare, "delta": delta, "delta_pct": delta_pct}
