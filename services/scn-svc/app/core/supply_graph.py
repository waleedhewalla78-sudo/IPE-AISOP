from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SupplyGraphNode:
    id: str
    name: str
    tier: int
    type: str


@dataclass
class SupplyGraphEdge:
    source_id: str
    target_id: str
    lead_time_days: int
    risk_score: float


def build_supply_graph(suppliers: list[dict]) -> dict:
    nodes: list[SupplyGraphNode] = []
    edges: list[SupplyGraphEdge] = []

    node_map: dict[str, SupplyGraphNode] = {}

    for supplier in suppliers:
        node = SupplyGraphNode(
            id=supplier["id"],
            name=supplier.get("name", supplier["id"]),
            tier=supplier.get("tier", 1),
            type=supplier.get("type", "supplier"),
        )
        nodes.append(node)
        node_map[node.id] = node

        for dep in supplier.get("dependencies", []):
            dep_id = dep.get("supplier_id", dep.get("id", ""))
            if dep_id and dep_id not in node_map:
                dep_node = SupplyGraphNode(
                    id=dep_id,
                    name=dep.get("name", dep_id),
                    tier=dep.get("tier", node.tier + 1),
                    type=dep.get("type", "supplier"),
                )
                nodes.append(dep_node)
                node_map[dep_id] = dep_node

            edge = SupplyGraphEdge(
                source_id=dep_id,
                target_id=node.id,
                lead_time_days=dep.get("lead_time_days", 7),
                risk_score=dep.get("risk_score", 0.5),
            )
            edges.append(edge)

    tier_summary: dict[int, list[str]] = {}
    for node in nodes:
        tier_summary.setdefault(node.tier, []).append(node.id)

    adjacency: dict[str, list[str]] = {}
    for edge in edges:
        adjacency.setdefault(edge.source_id, []).append(edge.target_id)

    return {
        "nodes": [{"id": n.id, "name": n.name, "tier": n.tier, "type": n.type} for n in nodes],
        "edges": [{"source_id": e.source_id, "target_id": e.target_id, "lead_time_days": e.lead_time_days, "risk_score": e.risk_score} for e in edges],
        "tier_summary": {str(k): v for k, v in tier_summary.items()},
        "adjacency": adjacency,
        "node_count": len(nodes),
        "edge_count": len(edges),
    }


def propagate_risk(
    graph: dict,
    at_risk_supplier_id: str,
    impact_probability: float,
) -> list[dict]:
    adjacency = graph.get("adjacency", {})
    nodes_by_id = {n["id"]: n for n in graph.get("nodes", [])}
    edges_by_source: dict[str, list[dict]] = {}
    for edge in graph.get("edges", []):
        edges_by_source.setdefault(edge["source_id"], []).append(edge)

    impacted: list[dict] = []

    visited: set[str] = set()
    queue: list[tuple[str, float, int]] = [(at_risk_supplier_id, impact_probability, 0)]
    visited.add(at_risk_supplier_id)

    impacted.append({
        "supplier_id": at_risk_supplier_id,
        "impact_probability": round(impact_probability, 4),
        "impact_level": "critical" if impact_probability > 0.7 else ("high" if impact_probability > 0.4 else "medium"),
        "depth": 0,
        "path": [at_risk_supplier_id],
    })

    while queue:
        current_id, current_prob, current_depth = queue.pop(0)
        for target_id in adjacency.get(current_id, []):
            if target_id in visited:
                continue
            visited.add(target_id)

            edge_data_list = edges_by_source.get(current_id, [])
            edge_risk = 0.5
            for e in edge_data_list:
                if e["target_id"] == target_id:
                    edge_risk = e["risk_score"]
                    break

            propagated_prob = round(current_prob * edge_risk, 4)
            if propagated_prob < 0.05:
                continue

            impact_level = "critical" if propagated_prob > 0.7 else ("high" if propagated_prob > 0.4 else "medium")
            if propagated_prob <= 0.2:
                impact_level = "low"

            impacted.append({
                "supplier_id": target_id,
                "impact_probability": propagated_prob,
                "impact_level": impact_level,
                "depth": current_depth + 1,
                "path": [at_risk_supplier_id, target_id],
            })

            if propagated_prob >= 0.05:
                queue.append((target_id, propagated_prob, current_depth + 1))

    impacted.sort(key=lambda x: x["impact_probability"], reverse=True)
    return impacted