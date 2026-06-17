import re

DELAY_KEYWORDS: dict[str, list[str]] = {
    "material_shortage": [
        "out of stock", "shortage", "missing material", "lack of", "stockout",
        "not available", "ran out", "insufficient", "raw material",
    ],
    "capacity_overload": [
        "no capacity", "overloaded", "queue", "backlog", "fully booked",
        "no available", "machine busy", "work center full",
    ],
    "labor_absence": [
        "absent", "sick", "unavailable", "no operator", "called out",
        "vacation", "no show", "short staffed",
    ],
    "supplier_delay": [
        "supplier late", "vendor delay", "shipment delayed", "po not received",
        "supplier missed", "order not arrived", "logistics delay",
    ],
    "maintenance": [
        "breakdown", "maintenance", "repair", "broken", "machine down",
        "equipment failure", "downtime", "not working",
    ],
    "quality_issue": [
        "quality", "defect", "rework", "scrap", "non-conforming",
        "failed inspection", "rejected", "out of spec",
    ],
    "process_variance": [
        "cycle time", "took longer", "unexpected", "variance", "delay in process",
        "waiting time", "setup issue",
    ],
}


def classify_by_rules(delay_data: dict) -> dict:
    source_text = str(delay_data.get("source_text", "")).lower()
    mo_status = str(delay_data.get("mo_status", "")).lower()
    work_center_status = str(delay_data.get("work_center_status", "")).lower()

    text = f"{source_text} {mo_status} {work_center_status}"

    scores: dict[str, float] = {}
    for category, keywords in DELAY_KEYWORDS.items():
        score = 0.0
        for kw in keywords:
            count = len(re.findall(re.escape(kw), text))
            score += count * (1.0 / len(keywords))
        if score > 0:
            scores[category] = min(score * 2.0, 0.95)

    if not scores:
        return {
            "cause_category": "other",
            "confidence": 0.3,
            "matched_keywords": [],
            "reason": "No delay pattern matched",
        }

    best = max(scores, key=scores.get)
    confidence = scores[best]

    return {
        "cause_category": best,
        "confidence": round(confidence, 4),
        "matched_keywords": [
            kw for kw in DELAY_KEYWORDS[best]
            if re.search(re.escape(kw), text)
        ],
        "reason": f"Matched {len(DELAY_KEYWORDS[best])} keywords in '{best}' category",
    }
