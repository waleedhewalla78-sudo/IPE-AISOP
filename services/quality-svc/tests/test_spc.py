import math

from app.core.spc import calculate_xbar_chart, calculate_p_chart


class TestXbarChart:
    def test_basic_xbar(self):
        measurements = [
            [10.0, 10.1, 9.9],
            [10.2, 10.0, 10.1],
            [9.8, 10.0, 10.2],
        ]
        result = calculate_xbar_chart(measurements)
        assert abs(result.mean - 10.0333) < 0.01
        assert result.std_dev > 0
        assert result.ucl > result.mean
        assert result.lcl < result.mean

    def test_out_of_control_point(self):
        measurements = [
            [10.0], [10.1], [9.9], [10.0], [10.2],
            [10.1], [9.8], [10.0], [10.1], [10.0],
            [10.0], [10.1], [9.9], [10.0], [20.0],
        ]
        result = calculate_xbar_chart(measurements)
        assert len(result.points_out_of_control) > 0

    def test_stable_process(self):
        measurements = [
            [10.0, 10.0, 10.0],
            [10.0, 10.0, 10.0],
            [10.0, 10.0, 10.0],
        ]
        result = calculate_xbar_chart(measurements)
        assert result.std_dev == 0.0
        assert len(result.points_out_of_control) == 0

    def test_cp_cpk_with_spec_limits(self):
        measurements = [
            [10.0, 10.1, 9.9],
            [10.2, 10.0, 10.1],
            [9.8, 10.0, 10.2],
        ]
        result = calculate_xbar_chart(measurements, usl=12.0, lsl=8.0)
        assert result.cp > 0
        assert result.cpk > 0

    def test_empty_measurements(self):
        result = calculate_xbar_chart([])
        assert result.mean == 0
        assert result.std_dev == 0

    def test_single_subgroup(self):
        result = calculate_xbar_chart([[10.0, 10.1, 9.9]])
        assert result.mean == 10.0


class TestPChart:
    def test_basic_pchart(self):
        result = calculate_p_chart(
            defect_counts=[2, 3, 1, 4, 2],
            sample_sizes=[100, 100, 100, 100, 100],
        )
        assert "p_bar" in result
        assert result["p_bar"] > 0
        assert "out_of_control" in result

    def test_all_defects(self):
        result = calculate_p_chart(
            defect_counts=[100, 100, 100],
            sample_sizes=[100, 100, 100],
        )
        assert result["p_bar"] == 1.0

    def test_no_defects(self):
        result = calculate_p_chart(
            defect_counts=[0, 0, 0],
            sample_sizes=[100, 100, 100],
        )
        assert result["p_bar"] == 0.0

    def test_empty(self):
        result = calculate_p_chart([], [])
        assert result["p_bar"] == 0

    def test_out_of_control_detection(self):
        result = calculate_p_chart(
            defect_counts=[2, 3, 2, 2, 50],
            sample_sizes=[100, 100, 100, 100, 100],
        )
        assert len(result["out_of_control"]) > 0