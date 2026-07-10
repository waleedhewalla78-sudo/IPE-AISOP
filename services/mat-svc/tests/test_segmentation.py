from app.core.segmentation import (
    calculate_demand_profile,
    classify_abc,
    classify_xyz,
    get_segment_policy,
)


def test_abc_classification_with_ten_products():
    products = [
        {"product_id": f"P{i}", "revenue_total": revenue}
        for i, revenue in enumerate([40, 40, 10, 5, 1, 1, 1, 1, 1, 1], start=1)
    ]

    results = classify_abc(products, a_threshold=80, b_threshold=95)
    counts = {klass: sum(1 for row in results if row["abc_class"] == klass) for klass in "ABC"}

    assert counts == {"A": 2, "B": 2, "C": 6}
    assert results[0]["abc_class"] == "A"
    assert results[-1]["abc_class"] == "C"


def test_xyz_boundaries():
    assert classify_xyz(0.5, x_threshold=0.5, y_threshold=1.0) == "X"
    assert classify_xyz(0.5001, x_threshold=0.5, y_threshold=1.0) == "Y"
    assert classify_xyz(1.0, x_threshold=0.5, y_threshold=1.0) == "Y"
    assert classify_xyz(1.0001, x_threshold=0.5, y_threshold=1.0) == "Z"


def test_zero_demand_is_z_segment():
    profile = calculate_demand_profile([0, 0, 0, 0], x_threshold=0.5, y_threshold=1.0)

    assert profile["xyz_class"] == "Z"
    assert profile["demand_mean"] == 0


def test_ax_policy_targets_99_percent_service_level():
    policy = get_segment_policy("A", "X")

    assert policy["combined_segment"] == "AX"
    assert policy["target_service_level_pct"] == 99.0
