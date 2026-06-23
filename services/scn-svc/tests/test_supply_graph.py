from app.core.supply_graph import SupplyGraphNode, SupplyGraphEdge, build_supply_graph, propagate_risk


class TestBuildSupplyGraph:
    def test_simple_graph(self):
        suppliers = [
            {"id": "supp-1", "name": "Primary Supplier", "tier": 1, "type": "supplier", "dependencies": []},
            {"id": "supp-2", "name": "Secondary Supplier", "tier": 1, "type": "supplier", "dependencies": []},
        ]
        result = build_supply_graph(suppliers)
        assert result["node_count"] == 2
        assert result["edge_count"] == 0
        assert "1" in result["tier_summary"]

    def test_graph_with_dependencies(self):
        suppliers = [
            {
                "id": "oem-1",
                "name": "OEM Assembly",
                "tier": 0,
                "type": "oem",
                "dependencies": [
                    {"supplier_id": "supp-1", "name": "Steel Co", "tier": 1, "lead_time_days": 7, "risk_score": 0.3},
                ],
            },
        ]
        result = build_supply_graph(suppliers)
        assert result["node_count"] == 2
        assert result["edge_count"] == 1
        assert result["edges"][0]["source_id"] == "supp-1"
        assert result["edges"][0]["target_id"] == "oem-1"

    def test_multi_tier_graph(self):
        suppliers = [
            {
                "id": "oem-1",
                "name": "OEM",
                "tier": 0,
                "type": "oem",
                "dependencies": [
                    {"supplier_id": "supp-1", "name": "Tier 1", "tier": 1, "lead_time_days": 14, "risk_score": 0.4},
                ],
            },
            {
                "id": "supp-1",
                "name": "Tier 1 Supplier",
                "tier": 1,
                "type": "supplier",
                "dependencies": [
                    {"supplier_id": "supp-2", "name": "Tier 2 Raw Material", "tier": 2, "lead_time_days": 21, "risk_score": 0.5},
                ],
            },
        ]
        result = build_supply_graph(suppliers)
        assert result["node_count"] >= 3
        assert result["edge_count"] >= 2
        assert "0" in result["tier_summary"]
        assert "1" in result["tier_summary"]
        assert "2" in result["tier_summary"]

    def test_empty_suppliers(self):
        result = build_supply_graph([])
        assert result["node_count"] == 0
        assert result["edge_count"] == 0

    def test_adjacency_map(self):
        suppliers = [
            {
                "id": "oem-1",
                "name": "OEM",
                "tier": 0,
                "type": "oem",
                "dependencies": [
                    {"supplier_id": "supp-1", "name": "S1", "tier": 1, "lead_time_days": 7, "risk_score": 0.3},
                    {"supplier_id": "supp-2", "name": "S2", "tier": 1, "lead_time_days": 10, "risk_score": 0.6},
                ],
            },
        ]
        result = build_supply_graph(suppliers)
        assert "supp-1" in result["adjacency"]
        assert "oem-1" in result["adjacency"]["supp-1"]
        assert "supp-2" in result["adjacency"]
        assert "oem-1" in result["adjacency"]["supp-2"]


class TestPropagateRisk:
    def _make_graph(self):
        suppliers = [
            {
                "id": "oem-1",
                "name": "OEM",
                "tier": 0,
                "type": "oem",
                "dependencies": [
                    {"supplier_id": "supp-1", "name": "Tier 1A", "tier": 1, "lead_time_days": 7, "risk_score": 0.6},
                    {"supplier_id": "supp-2", "name": "Tier 1B", "tier": 1, "lead_time_days": 10, "risk_score": 0.4},
                ],
            },
            {
                "id": "supp-1",
                "name": "Tier 1A",
                "tier": 1,
                "type": "supplier",
                "dependencies": [
                    {"supplier_id": "supp-3", "name": "Tier 2 Raw", "tier": 2, "lead_time_days": 21, "risk_score": 0.5},
                ],
            },
        ]
        return build_supply_graph(suppliers)

    def test_propagate_single_source(self):
        graph = self._make_graph()
        impacted = propagate_risk(graph, "supp-2", 0.8)
        assert len(impacted) >= 1
        assert impacted[0]["supplier_id"] == "supp-2"

    def test_propagate_cascading(self):
        graph = self._make_graph()
        impacted = propagate_risk(graph, "supp-3", 0.9)
        source_ids = [i["supplier_id"] for i in impacted]
        assert "supp-3" in source_ids
        assert "supp-1" in source_ids
        assert "oem-1" in source_ids

    def test_propagate_probability_decreases(self):
        graph = self._make_graph()
        impacted = propagate_risk(graph, "supp-3", 0.9)
        source_prob = None
        tier1_prob = None
        for i in impacted:
            if i["supplier_id"] == "supp-3":
                source_prob = i["impact_probability"]
            elif i["supplier_id"] == "supp-1":
                tier1_prob = i["impact_probability"]
        if source_prob and tier1_prob:
            assert tier1_prob < source_prob

    def test_propagate_low_probability_filtered(self):
        suppliers = [
            {"id": "src", "name": "Source", "tier": 1, "type": "supplier", "dependencies": [
                {"supplier_id": "tgt", "name": "Target", "tier": 2, "lead_time_days": 30, "risk_score": 0.01},
            ]},
        ]
        graph = build_supply_graph(suppliers)
        impacted = propagate_risk(graph, "src", 0.1)
        source_ids = [i["supplier_id"] for i in impacted]
        assert "src" in source_ids
        assert "tgt" not in source_ids

    def test_impact_levels(self):
        suppliers = [
            {"id": "s1", "name": "S1", "tier": 1, "type": "supplier", "dependencies": [
                {"supplier_id": "s2", "name": "S2", "tier": 2, "lead_time_days": 7, "risk_score": 0.8},
            ]},
        ]
        graph = build_supply_graph(suppliers)
        impacted = propagate_risk(graph, "s1", 0.9)
        source = next(i for i in impacted if i["supplier_id"] == "s1")
        assert source["impact_level"] in ("critical", "high", "medium", "low")

    def test_propagate_sorted_by_probability(self):
        graph = self._make_graph()
        impacted = propagate_risk(graph, "supp-3", 0.9)
        probs = [i["impact_probability"] for i in impacted]
        assert probs == sorted(probs, reverse=True)

    def test_nonexistent_source(self):
        suppliers = [{"id": "s1", "name": "S1", "tier": 1, "type": "supplier", "dependencies": []}]
        graph = build_supply_graph(suppliers)
        impacted = propagate_risk(graph, "nonexistent", 0.9)
        assert len(impacted) == 1
        assert impacted[0]["impact_level"] == "critical"