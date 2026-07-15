"""B1.4 Action tracker — decisions with owners and outcomes."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4


class ActionTracker:
    def __init__(self) -> None:
        self._items: list[dict[str, Any]] = []

    def create(
        self,
        *,
        title: str,
        owner: str,
        source: str = "planner",
        due: str | None = None,
        mo_id: str | None = None,
    ) -> dict[str, Any]:
        item = {
            "action_id": f"ACT-{uuid4().hex[:8].upper()}",
            "title": title,
            "owner": owner,
            "source": source,
            "mo_id": mo_id,
            "due": due,
            "status": "open",
            "created_at": datetime.now(UTC).isoformat(),
            "outcome": None,
        }
        self._items.append(item)
        return item

    def complete(self, action_id: str, outcome: str) -> dict[str, Any] | None:
        for item in self._items:
            if item["action_id"] == action_id:
                item["status"] = "done"
                item["outcome"] = outcome
                item["completed_at"] = datetime.now(UTC).isoformat()
                return item
        return None

    def list(self, *, status: str | None = None) -> list[dict[str, Any]]:
        if status:
            return [i for i in self._items if i["status"] == status]
        return list(self._items)

    def clear(self) -> None:
        self._items.clear()
