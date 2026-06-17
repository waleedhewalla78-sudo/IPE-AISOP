"""LLM-based delay classification using Anthropic SDK."""

import os

_CATEGORIES = [
    "material_shortage",
    "capacity_overload",
    "labor_absence",
    "supplier_delay",
    "maintenance",
    "quality_issue",
    "process_variance",
    "other",
]


async def classify_by_llm(source_text: str) -> dict:
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return {
            "cause_category": "other", "confidence": 0.0,
            "cause_detail": "API key not configured",
        }

    try:
        import anthropic

        client = anthropic.AsyncAnthropic(api_key=api_key)
        categories_str = ", ".join(_CATEGORIES)
        prompt = (
            "Classify the following manufacturing delay report into exactly one"
            f" category: {categories_str}.\n"
            "Reply with only the category name and a confidence score"
            " (0-1) separated by a pipe.\n"
            "Example: material_shortage|0.85\n\n"
            f"Report: {source_text}"
        )

        message = await client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=50,
            messages=[{"role": "user", "content": prompt}],
        )
        content = message.content[0].text.strip() if message.content else ""
    except Exception as exc:
        return {"cause_category": "other", "confidence": 0.0, "cause_detail": str(exc)}

    if "|" in content:
        parts = content.rsplit("|", 1)
        category = parts[0].strip().lower()
        try:
            confidence = min(max(float(parts[1].strip()), 0.0), 1.0)
        except ValueError:
            confidence = 0.0
        if category not in _CATEGORIES:
            category = "other"
    else:
        category = "other"
        confidence = 0.0

    return {
        "cause_category": category,
        "confidence": round(confidence, 4),
        "cause_detail": content,
    }
