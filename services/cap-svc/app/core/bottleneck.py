from collections import defaultdict


def detect_bottlenecks(
    assignments: list[dict],
    work_centers: list[dict],
    horizon_minutes: int = 10080,
) -> list[dict]:
    wc_hours: dict[str, float] = defaultdict(float)
    wc_capacity: dict[str, float] = {}
    wc_names: dict[str, str] = {}

    for wc in work_centers:
        wc_id = wc.get("id", "")
        wc_capacity[wc_id] = float(wc.get("capacity_hours_per_day", 8)) * (horizon_minutes / 1440)
        wc_names[wc_id] = wc.get("name", wc_id)

    for a in assignments:
        wc_id = a.get("work_center_id", "")
        duration = a.get("duration", 0)
        wc_hours[wc_id] += duration / 60.0

    bottlenecks = []
    for wc_id, used_hours in wc_hours.items():
        cap = wc_capacity.get(wc_id, 1)
        util_pct = (used_hours / cap * 100) if cap > 0 else 0
        bottlenecks.append({
            "work_center_id": wc_id,
            "work_center_name": wc_names.get(wc_id, wc_id),
            "total_load_hours": round(used_hours, 2),
            "capacity_hours": round(cap, 2),
            "utilization_pct": round(util_pct, 1),
            "is_bottleneck": util_pct > 85,
            "severity": (
                "critical" if util_pct > 95
                else "high" if util_pct > 85
                else "medium" if util_pct > 70
                else "low"
            ),
        })

    bottlenecks.sort(key=lambda b: b["utilization_pct"], reverse=True)
    return bottlenecks
