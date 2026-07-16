"""Phase 7 §4.2 — Labour Planning (skills matrix + single-point-of-failure flags)."""

from __future__ import annotations

from typing import Any

# skill → operators that hold it as primary (★) or cross-trained (✓)
_DEFAULT_OPERATORS = [
    {
        "name": "Mohamed",
        "shift": "A",
        "skills": {
            "Core Cut": "cross",
            "Winding": "primary",
            "Assembly": "cross",
            "Painting": "cross",
        },
        "certified": ["DT100", "DT250", "PT500"],
    },
    {
        "name": "Sara",
        "shift": "A",
        "skills": {"Winding": "primary", "Assembly": "cross", "Testing": "cross"},
        "certified": ["DT100", "DT250"],
    },
    {
        "name": "Ahmed",
        "shift": "A",
        "skills": {
            "Core Cut": "cross",
            "Assembly": "primary",
            "Testing": "cross",
            "Painting": "cross",
        },
        "certified": ["all"],
    },
    {
        "name": "Fatima",
        "shift": "A",
        "skills": {"Testing": "primary", "Painting": "cross"},
        "certified": ["all"],
    },
    {
        "name": "Hassan",
        "shift": "A",
        "skills": {"Core Cut": "primary", "Testing": "cross", "Painting": "primary"},
        "certified": ["all"],
    },
]


def plan_labour(
    *,
    week: str = "W31",
    operators: list[dict[str, Any]] | None = None,
    critical_skill: str = "Winding",
    critical_cert: str = "PT500",
) -> dict[str, Any]:
    """Assign primary operators per skill and flag single-point-of-failure risks."""

    operators = operators or _DEFAULT_OPERATORS

    # Build skill → capable-operator index.
    skill_index: dict[str, list[str]] = {}
    for op in operators:
        for skill, _level in op.get("skills", {}).items():
            skill_index.setdefault(skill, []).append(op["name"])

    # Certification index for the critical cert.
    cert_capable = [
        op["name"]
        for op in operators
        if critical_cert in op.get("certified", []) or "all" in op.get("certified", [])
    ]
    # Operators who can BOTH do the critical skill AND hold the critical cert.
    critical_capable = [
        op["name"]
        for op in operators
        if critical_skill in op.get("skills", {})
        and (critical_cert in op.get("certified", []) or "all" in op.get("certified", []))
    ]

    spof_flags: list[dict[str, Any]] = []
    if len(critical_capable) <= 1:
        only = critical_capable[0] if critical_capable else "nobody"
        # Suggest a cross-train candidate: someone with the skill but not the cert.
        candidate = next(
            (
                op["name"]
                for op in operators
                if critical_skill in op.get("skills", {}) and op["name"] != only
            ),
            None,
        )
        spof_flags.append(
            {
                "skill": critical_skill,
                "certification": critical_cert,
                "only_operator": only,
                "risk": (
                    f"If {only} is absent, all {critical_cert} {critical_skill} production stops."
                ),
                "recommendation": (
                    f"Cross-train {candidate} on {critical_cert} (est. 2-day program)"
                    if candidate
                    else "Recruit/cross-train a second certified operator"
                ),
                "cross_train_candidate": candidate,
            }
        )

    assignments = [
        {"work_centre": skill, "primary": ops[0], "backups": ops[1:]}
        for skill, ops in sorted(skill_index.items())
    ]

    return {
        "week": week,
        "skills_matrix": [
            {
                "operator": op["name"],
                "shift": op["shift"],
                "skills": op["skills"],
                "certified": op["certified"],
            }
            for op in operators
        ],
        "assignments": assignments,
        "certified_for": {critical_cert: cert_capable},
        "single_point_of_failure": spof_flags,
        "spof_count": len(spof_flags),
    }
