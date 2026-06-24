"""Visual CPM — critical path, slack, and cascade scheduling."""

from __future__ import annotations

from collections import defaultdict, deque
from datetime import UTC, datetime, timedelta
from typing import Any


def _parse_dt(value: str | datetime | None) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=UTC)
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def _build_graph(operations: list[dict]) -> tuple[dict[str, dict], dict[str, list[str]], dict[str, list[str]]]:
    nodes: dict[str, dict] = {}
    successors: dict[str, list[str]] = defaultdict(list)
    predecessors: dict[str, list[str]] = defaultdict(list)

    by_mo: dict[str, list[dict]] = defaultdict(list)
    for op in operations:
        op_id = str(op["operation_id"])
        nodes[op_id] = op
        by_mo[str(op.get("mo_id", ""))].append(op)

    for mo_ops in by_mo.values():
        sorted_ops = sorted(mo_ops, key=lambda o: int(o.get("sequence") or 0))
        for idx in range(len(sorted_ops) - 1):
            a = str(sorted_ops[idx]["operation_id"])
            b = str(sorted_ops[idx + 1]["operation_id"])
            successors[a].append(b)
            predecessors[b].append(a)

    for op in operations:
        for succ in op.get("successors") or []:
            a = str(op["operation_id"])
            b = str(succ)
            if b not in successors[a]:
                successors[a].append(b)
            if a not in predecessors[b]:
                predecessors[b].append(a)

    return nodes, dict(successors), dict(predecessors)


def compute_critical_path(operations: list[dict]) -> list[str]:
    """Return operation IDs on the longest path through the dependency graph."""
    if not operations:
        return []

    nodes, successors, predecessors = _build_graph(operations)
    durations: dict[str, float] = {}
    for op_id, op in nodes.items():
        start = _parse_dt(op.get("planned_start"))
        end = _parse_dt(op.get("planned_end"))
        if start and end:
            durations[op_id] = max(1.0, (end - start).total_seconds() / 60.0)
        else:
            durations[op_id] = float(op.get("duration_minutes") or op.get("duration") or 60)

    memo: dict[str, tuple[float, list[str]]] = {}

    def longest_path(op_id: str) -> tuple[float, list[str]]:
        if op_id in memo:
            return memo[op_id]
        best_len = durations.get(op_id, 0.0)
        best_path = [op_id]
        for succ in successors.get(op_id, []):
            succ_len, succ_path = longest_path(succ)
            total = durations.get(op_id, 0.0) + succ_len
            if total > best_len:
                best_len = total
                best_path = [op_id] + succ_path
        memo[op_id] = (best_len, best_path)
        return best_len, best_path

    roots = [op_id for op_id in nodes if not predecessors.get(op_id)]
    if not roots:
        roots = list(nodes.keys())

    best: list[str] = []
    best_total = -1.0
    for root in roots:
        total, path = longest_path(root)
        if total > best_total:
            best_total = total
            best = path
    return best


def compute_slack(operations: list[dict]) -> dict[str, int]:
    """Compute slack minutes per operation (total float)."""
    if not operations:
        return {}

    nodes, successors, predecessors = _build_graph(operations)
    es: dict[str, float] = {}
    ef: dict[str, float] = {}

    for op_id, op in nodes.items():
        start = _parse_dt(op.get("planned_start"))
        end = _parse_dt(op.get("planned_end"))
        if start and end:
            es[op_id] = 0.0
            ef[op_id] = max(1.0, (end - start).total_seconds() / 60.0)
        else:
            dur = float(op.get("duration_minutes") or op.get("duration") or 60)
            es[op_id] = 0.0
            ef[op_id] = dur

    topo: list[str] = []
    indegree = {op_id: len(predecessors.get(op_id, [])) for op_id in nodes}
    queue = deque([op_id for op_id, deg in indegree.items() if deg == 0])
    while queue:
        node = queue.popleft()
        topo.append(node)
        for succ in successors.get(node, []):
            es[succ] = max(es.get(succ, 0.0), ef.get(node, 0.0))
            ef[succ] = es[succ] + (ef.get(succ, 0.0) - es.get(node, 0.0))
            indegree[succ] -= 1
            if indegree[succ] == 0:
                queue.append(succ)

    project_end = max(ef.values()) if ef else 0.0
    ls: dict[str, float] = {}
    lf: dict[str, float] = {}
    for op_id in reversed(topo):
        if not successors.get(op_id):
            lf[op_id] = project_end
        else:
            lf[op_id] = min(lf.get(s, project_end) for s in successors[op_id])
        ls[op_id] = lf[op_id] - (ef.get(op_id, 0.0) - es.get(op_id, 0.0))

    return {op_id: int(max(0.0, ls.get(op_id, 0.0) - es.get(op_id, 0.0))) for op_id in nodes}


def _detect_conflicts(operations: list[dict]) -> list[dict]:
    """Detect work-center capacity overlaps after cascade."""
    by_wc: dict[str, list[dict]] = defaultdict(list)
    for op in operations:
        wc_id = op.get("work_center_id")
        if wc_id:
            by_wc[str(wc_id)].append(op)

    conflicts: list[dict] = []
    for wc_id, ops in by_wc.items():
        sorted_ops = sorted(
            ops,
            key=lambda o: _parse_dt(o.get("planned_start")) or datetime.min.replace(tzinfo=UTC),
        )
        for i in range(len(sorted_ops) - 1):
            a = sorted_ops[i]
            b = sorted_ops[i + 1]
            a_end = _parse_dt(a.get("planned_end"))
            b_start = _parse_dt(b.get("planned_start"))
            if a_end and b_start and a_end > b_start:
                conflicts.append(
                    {
                        "operation_id": str(b.get("operation_id")),
                        "reason": f"WC {wc_id} capacity exceeded at {b_start.date().isoformat()}",
                    }
                )
    return conflicts


def cascade_schedule(
    operations: list[dict],
    *,
    mo_id: str,
    operation_id: str,
    delta_minutes: int,
) -> dict[str, Any]:
    """Shift an operation and propagate to successors; return updated ops + metadata."""
    ops = [dict(op) for op in operations]
    nodes, successors, _ = _build_graph(ops)
    target = str(operation_id)
    if target not in nodes:
        return {"operations": ops, "critical_path_ids": [], "conflicts": [{"operation_id": target, "reason": "operation_not_found"}]}

    affected: set[str] = set()
    queue = deque([target])
    while queue:
        op_id = queue.popleft()
        if op_id in affected:
            continue
        affected.add(op_id)
        for succ in successors.get(op_id, []):
            queue.append(succ)

    delta = timedelta(minutes=delta_minutes)
    for op in ops:
        op_id = str(op["operation_id"])
        if op_id not in affected:
            continue
        start = _parse_dt(op.get("planned_start"))
        end = _parse_dt(op.get("planned_end"))
        if start and end:
            op["planned_start"] = (start + delta).isoformat()
            op["planned_end"] = (end + delta).isoformat()

    critical_path_ids = compute_critical_path(ops)
    slack_map = compute_slack(ops)
    for op in ops:
        op_id = str(op["operation_id"])
        op["slack_minutes"] = slack_map.get(op_id, 0)
        op["is_critical"] = op_id in critical_path_ids

    conflicts = _detect_conflicts(ops)
    return {
        "operations": ops,
        "critical_path_ids": critical_path_ids,
        "conflicts": conflicts,
        "mo_id": mo_id,
    }
