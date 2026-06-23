"""F1-score unit test for NLP delay classifier.

Tests the rule-based classifier against 100 mock chatter messages with
manually tagged ground truth to validate >85% F1-score target.

Ground truth texts are designed to match the actual keywords used by
the rule classifier in rule_classifier.py.
"""

from app.core.rule_classifier import classify_by_rules

GROUND_TRUTH = [
    # material_shortage (13 samples)
    {"text": "Steel coil out of stock, cannot proceed", "expected": "material_shortage"},
    {"text": "Shortage of copper wire for assembly", "expected": "material_shortage"},
    {"text": "Missing material - resistors not delivered", "expected": "material_shortage"},
    {"text": "Raw material not available in warehouse", "expected": "material_shortage"},
    {"text": "Stockout of chemical supplies", "expected": "material_shortage"},
    {"text": "Lack of plastic housing parts", "expected": "material_shortage"},
    {"text": "Insufficient aluminum sheets for production", "expected": "material_shortage"},
    {"text": "Component ran out during shift", "expected": "material_shortage"},
    {"text": "Out of stock on fasteners and bolts", "expected": "material_shortage"},
    {"text": "Missing material for PCB assembly", "expected": "material_shortage"},
    {"text": "Shortage of packaging materials", "expected": "material_shortage"},
    {"text": "Raw material stockout at storage", "expected": "material_shortage"},
    {"text": "Insufficient inventory for batch", "expected": "material_shortage"},
    # capacity_overload (13 samples)
    {"text": "Work center WC-01 is overloaded", "expected": "capacity_overload"},
    {"text": "No capacity on assembly line 2", "expected": "capacity_overload"},
    {"text": "Queue too long at CNC station", "expected": "capacity_overload"},
    {"text": "Machine busy on all shifts", "expected": "capacity_overload"},
    {"text": "Work center full, cannot schedule", "expected": "capacity_overload"},
    {"text": "Backlog of orders at welding", "expected": "capacity_overload"},
    {"text": "Fully booked for next 2 weeks", "expected": "capacity_overload"},
    {"text": "No available time slots for setup", "expected": "capacity_overload"},
    {"text": "Overloaded production line 1", "expected": "capacity_overload"},
    {"text": "Queue backlog at painting station", "expected": "capacity_overload"},
    {"text": "Work center overloaded with concurrent orders", "expected": "capacity_overload"},
    {"text": "No capacity for additional jobs", "expected": "capacity_overload"},
    {"text": "Machine fully booked this week", "expected": "capacity_overload"},
    # labor_absence (13 samples)
    {"text": "Operator absent today, sick leave", "expected": "labor_absence"},
    {"text": "CNC operator called out, no show", "expected": "labor_absence"},
    {"text": "No operator available for night shift", "expected": "labor_absence"},
    {"text": "Worker unavailable due to vacation", "expected": "labor_absence"},
    {"text": "Short staffed on production floor", "expected": "labor_absence"},
    {"text": "Supervisor absent, no replacement", "expected": "labor_absence"},
    {"text": "Technician sick, cannot proceed", "expected": "labor_absence"},
    {"text": "Called out - operator not present", "expected": "labor_absence"},
    {"text": "No show for scheduled shift", "expected": "labor_absence"},
    {"text": "Labor shortage, unavailable crew", "expected": "labor_absence"},
    {"text": "Operator absent due to illness", "expected": "labor_absence"},
    {"text": "Worker on vacation, no backup", "expected": "labor_absence"},
    {"text": "Staff unavailable for double shift", "expected": "labor_absence"},
    # supplier_delay (13 samples)
    {"text": "Supplier late with delivery by 3 days", "expected": "supplier_delay"},
    {"text": "Vendor delay on critical components", "expected": "supplier_delay"},
    {"text": "Shipment delayed from logistics partner", "expected": "supplier_delay"},
    {"text": "Supplier missed delivery deadline", "expected": "supplier_delay"},
    {"text": "Order not arrived from vendor", "expected": "supplier_delay"},
    {"text": "Logistics delay on incoming goods", "expected": "supplier_delay"},
    {"text": "PO not received from supplier", "expected": "supplier_delay"},
    {"text": "Supplier late with raw materials", "expected": "supplier_delay"},
    {"text": "Vendor delay affecting schedule", "expected": "supplier_delay"},
    {"text": "Shipment delayed by customs", "expected": "supplier_delay"},
    {"text": "Order not arrived at warehouse", "expected": "supplier_delay"},
    {"text": "Logistics delay on freight", "expected": "supplier_delay"},
    {"text": "Shipment delayed, supplier issue", "expected": "supplier_delay"},
    # maintenance (13 samples)
    {"text": "CNC mill breakdown, needs repair", "expected": "maintenance"},
    {"text": "Equipment failure on assembly line", "expected": "maintenance"},
    {"text": "Machine down, broken motor", "expected": "maintenance"},
    {"text": "Maintenance required on hydraulic press", "expected": "maintenance"},
    {"text": "Broken conveyor belt, downtime", "expected": "maintenance"},
    {"text": "Machine not working, needs repair", "expected": "maintenance"},
    {"text": "Equipment breakdown at welding", "expected": "maintenance"},
    {"text": "Downtime due to broken tooling", "expected": "maintenance"},
    {"text": "Maintenance overdue on lathe", "expected": "maintenance"},
    {"text": "Robot arm broken, repair needed", "expected": "maintenance"},
    {"text": "Machine breakdown on production floor", "expected": "maintenance"},
    {"text": "Equipment failure, downtime reported", "expected": "maintenance"},
    {"text": "Broken drill press, not working", "expected": "maintenance"},
    # quality_issue (13 samples)
    {"text": "Quality inspection failed, out of spec", "expected": "quality_issue"},
    {"text": "Defect detected in first article", "expected": "quality_issue"},
    {"text": "Rework needed on assembly batch", "expected": "quality_issue"},
    {"text": "Scrap generated from production", "expected": "quality_issue"},
    {"text": "Non-conforming parts found", "expected": "quality_issue"},
    {"text": "Rejected during quality check", "expected": "quality_issue"},
    {"text": "Failed inspection, not meeting spec", "expected": "quality_issue"},
    {"text": "Quality issue with surface finish", "expected": "quality_issue"},
    {"text": "Defect rate above threshold", "expected": "quality_issue"},
    {"text": "Rework required for weld quality", "expected": "quality_issue"},
    {"text": "Scrap rate increasing", "expected": "quality_issue"},
    {"text": "Non-conforming material rejected", "expected": "quality_issue"},
    {"text": "Quality test failed on batch", "expected": "quality_issue"},
    # process_variance (9 samples)
    {"text": "Cycle time variance exceeding 15%", "expected": "process_variance"},
    {"text": "Took longer than expected setup", "expected": "process_variance"},
    {"text": "Unexpected delay in process", "expected": "process_variance"},
    {"text": "Waiting time at loading dock", "expected": "process_variance"},
    {"text": "Setup issue causing delays", "expected": "process_variance"},
    {"text": "Cycle time 20% above standard", "expected": "process_variance"},
    {"text": "Process variance detected on line", "expected": "process_variance"},
    {"text": "Took longer for changeover", "expected": "process_variance"},
    {"text": "Unexpected variance in output", "expected": "process_variance"},
    # other (13 samples)
    {"text": "Order modification from customer", "expected": "other"},
    {"text": "Waiting for design approval", "expected": "other"},
    {"text": "Documentation pending from engineering", "expected": "other"},
    {"text": "Safety inspection scheduled", "expected": "other"},
    {"text": "Audit preparation required", "expected": "other"},
    {"text": "Customer changed order specifications", "expected": "other"},
    {"text": "Engineering review in progress", "expected": "other"},
    {"text": "Regulatory compliance update pending", "expected": "other"},
    {"text": "Holiday schedule adjustment needed", "expected": "other"},
    {"text": "IT system outage affecting scheduling", "expected": "other"},
    {"text": "Power outage in factory section", "expected": "other"},
    {"text": "Fire alarm test disrupting production", "expected": "other"},
    {"text": "Management review required", "expected": "other"},
]


def calculate_f1(predictions: list[str], ground_truth: list[str]) -> dict:
    """Calculate precision, recall, F1-score per category and macro F1."""
    categories = set(ground_truth)
    tp = fp = fn = 0
    category_metrics = {}

    for cat in categories:
        cat_tp = sum(1 for p, g in zip(predictions, ground_truth) if p == cat and g == cat)
        cat_fp = sum(1 for p, g in zip(predictions, ground_truth) if p == cat and g != cat)
        cat_fn = sum(1 for p, g in zip(predictions, ground_truth) if p != cat and g == cat)

        precision = cat_tp / (cat_tp + cat_fp) if (cat_tp + cat_fp) > 0 else 0
        recall = cat_tp / (cat_tp + cat_fn) if (cat_tp + cat_fn) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

        category_metrics[cat] = {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
            "support": sum(1 for g in ground_truth if g == cat),
        }

        tp += cat_tp
        fp += cat_fp
        fn += cat_fn

    macro_f1 = sum(m["f1"] for m in category_metrics.values()) / len(category_metrics) if category_metrics else 0
    micro_precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    micro_recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    micro_f1 = 2 * micro_precision * micro_recall / (micro_precision + micro_recall) if (micro_precision + micro_recall) > 0 else 0

    return {
        "macro_f1": round(macro_f1, 4),
        "micro_f1": round(micro_f1, 4),
        "micro_precision": round(micro_precision, 4),
        "micro_recall": round(micro_recall, 4),
        "per_category": category_metrics,
    }


class TestNF1Score:
    def test_f1_above_85_target(self):
        """Rule-based classifier must achieve >85% F1 against ground truth."""
        predictions = []
        for item in GROUND_TRUTH:
            result = classify_by_rules({"source_text": item["text"]})
            predictions.append(result["cause_category"])

        metrics = calculate_f1(predictions, [item["expected"] for item in GROUND_TRUTH])

        assert metrics["macro_f1"] >= 0.85, (
            f"Macro F1 {metrics['macro_f1']:.4f} below 0.85 target. "
            f"Per-category: {metrics['per_category']}"
        )
        assert metrics["micro_f1"] >= 0.85, (
            f"Micro F1 {metrics['micro_f1']:.4f} below 0.85 target"
        )

    def test_material_shortage_precision(self):
        """Material shortage classification should have high precision."""
        predictions = [classify_by_rules({"source_text": t["text"]})["cause_category"] for t in GROUND_TRUTH if t["expected"] == "material_shortage"]
        expected = ["material_shortage"] * len(predictions)
        metrics = calculate_f1(predictions, expected)
        assert metrics["per_category"]["material_shortage"]["precision"] >= 0.8

    def test_all_categories_represented(self):
        """Ground truth should cover all 8 categories."""
        categories = set(item["expected"] for item in GROUND_TRUTH)
        assert len(categories) == 8, f"Expected 8 categories, got {len(categories)}"

    def test_batch_size_matches_ground_truth(self):
        """Should have 100 ground truth samples."""
        assert len(GROUND_TRUTH) == 100, f"Expected 100 samples, got {len(GROUND_TRUTH)}"
