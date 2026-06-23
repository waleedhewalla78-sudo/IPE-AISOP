from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class SPCResult:
    mean: float
    std_dev: float
    ucl: float
    lcl: float
    points_out_of_control: list[int]
    runs: list[dict]
    cp: float
    cpk: float


def calculate_xbar_chart(
    measurements: list[list[float]],
    sigma_multiplier: float = 3.0,
    usl: float | None = None,
    lsl: float | None = None,
) -> SPCResult:
    if not measurements:
        return SPCResult(mean=0, std_dev=0, ucl=0, lcl=0, points_out_of_control=[], runs=[], cp=0, cpk=0)

    subgroup_means = [sum(g) / len(g) for g in measurements if g]
    if not subgroup_means:
        return SPCResult(mean=0, std_dev=0, ucl=0, lcl=0, points_out_of_control=[], runs=[], cp=0, cpk=0)

    overall_mean = sum(subgroup_means) / len(subgroup_means)

    if len(subgroup_means) > 1:
        std_dev = math.sqrt(sum((x - overall_mean) ** 2 for x in subgroup_means) / len(subgroup_means))
    else:
        all_values = [v for g in measurements for v in g]
        std_dev = math.sqrt(sum((x - overall_mean) ** 2 for x in all_values) / len(all_values)) if len(all_values) > 1 else 0.0

    ucl = overall_mean + sigma_multiplier * std_dev
    lcl = overall_mean - sigma_multiplier * std_dev

    points_out_of_control = []
    for i, m in enumerate(subgroup_means):
        if m > ucl or m < lcl:
            points_out_of_control.append(i)

    runs = _detect_runs(subgroup_means, overall_mean)

    cp = 0.0
    cpk = 0.0
    if usl is not None and lsl is not None and std_dev > 0:
        cp = (usl - lsl) / (6 * std_dev)
        cpu = (usl - overall_mean) / (3 * std_dev)
        cpl = (overall_mean - lsl) / (3 * std_dev)
        cpk = min(cpu, cpl)

    return SPCResult(
        mean=round(overall_mean, 4),
        std_dev=round(std_dev, 4),
        ucl=round(ucl, 4),
        lcl=round(lcl, 4),
        points_out_of_control=points_out_of_control,
        runs=runs,
        cp=round(cp, 4),
        cpk=round(cpk, 4),
    )


def calculate_p_chart(
    defect_counts: list[int],
    sample_sizes: list[int],
    sigma_multiplier: float = 3.0,
) -> dict:
    if not defect_counts or not sample_sizes:
        return {"ucl": 0, "lcl": 0, "p_bar": 0, "out_of_control": [], "cp": 0, "cpk": 0}

    total_defects = sum(defect_counts)
    total_inspected = sum(sample_sizes)
    p_bar = total_defects / total_inspected if total_inspected > 0 else 0

    results = []
    out_of_control = []

    for i, (d, n) in enumerate(zip(defect_counts, sample_sizes)):
        if n > 0:
            pi = d / n
            std_p = math.sqrt(p_bar * (1 - p_bar) / n) if n > 0 else 0
            ucl_i = min(1.0, p_bar + sigma_multiplier * std_p)
            lcl_i = max(0.0, p_bar - sigma_multiplier * std_p)
            results.append({
                "sample": i, "defect_rate": round(pi, 4),
                "ucl": round(ucl_i, 4), "lcl": round(lcl_i, 4),
                "out_of_control": pi > ucl_i or pi < lcl_i,
            })
            if pi > ucl_i or pi < lcl_i:
                out_of_control.append(i)

    return {
        "p_bar": round(p_bar, 4),
        "ucl": round(p_bar + sigma_multiplier * math.sqrt(p_bar * (1 - p_bar) / (sum(sample_sizes) / len(sample_sizes))), 4) if sample_sizes else 0,
        "lcl": round(max(0, p_bar - sigma_multiplier * math.sqrt(p_bar * (1 - p_bar) / (sum(sample_sizes) / len(sample_sizes)))), 4) if sample_sizes else 0,
        "out_of_control": out_of_control,
        "samples": results,
    }


def _detect_runs(means: list[float], center_line: float) -> list[dict]:
    runs = []
    current_direction = None
    run_start = 0
    run_length = 0

    for i, m in enumerate(means):
        if m > center_line:
            direction = "above"
        elif m < center_line:
            direction = "below"
        else:
            direction = "on"

        if direction != current_direction and current_direction is not None:
            if run_length >= 7:
                runs.append({"start": run_start, "length": run_length, "direction": current_direction, "type": "run_rule"})
            run_start = i
            run_length = 1
        else:
            run_length += 1
        current_direction = direction

    if run_length >= 7:
        runs.append({"start": run_start, "length": run_length, "direction": current_direction, "type": "run_rule"})

    for i, m in enumerate(means):
        if i >= 6:
            trend = all(means[j] > means[j - 1] for j in range(i - 5, i + 1) if j > 0)
            downtrend = all(means[j] < means[j - 1] for j in range(i - 5, i + 1) if j > 0)
            if trend:
                runs.append({"start": i - 5, "length": 6, "direction": "up", "type": "trend_rule"})
            if downtrend:
                runs.append({"start": i - 5, "length": 6, "direction": "down", "type": "trend_rule"})

    return runs