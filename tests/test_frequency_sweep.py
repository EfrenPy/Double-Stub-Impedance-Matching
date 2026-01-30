"""Tests for frequency sweep analysis."""

import numpy as np
import pytest

from double_stub.core import DoubleStubMatcher
from double_stub.frequency_sweep import FrequencySweepResult, frequency_sweep


@pytest.fixture
def sweep_matcher():
    return DoubleStubMatcher(
        distance_to_first_stub=0.07,
        distance_between_stubs=3.0 / 8.0,
        load_impedance=complex(38.9, -26.7),
        line_impedance=50.0,
        stub_impedance=50.0,
        stub_type='short',
        precision=1e-8,
    )


class TestFrequencySweep:
    def test_correct_point_count(self, sweep_matcher):
        solutions = sweep_matcher.calculate()
        l1, l2 = solutions[0]
        result = frequency_sweep(
            sweep_matcher, l1, l2,
            center_freq=1e9, freq_start=0.5e9, freq_stop=1.5e9,
            num_points=51,
        )
        assert len(result.frequencies) == 51
        assert len(result.reflection_coefficient) == 51
        assert len(result.vswr) == 51
        assert len(result.return_loss_db) == 51

    def test_center_freq_has_best_match(self, sweep_matcher):
        solutions = sweep_matcher.calculate()
        l1, l2 = solutions[0]
        result = frequency_sweep(
            sweep_matcher, l1, l2,
            center_freq=1e9, freq_start=0.5e9, freq_stop=1.5e9,
            num_points=101,
        )
        center_idx = np.argmin(np.abs(result.frequencies - 1e9))
        gamma_at_center = result.reflection_coefficient[center_idx]
        # Center frequency should have very low reflection
        assert gamma_at_center < 0.01

    def test_vswr_always_ge_one(self, sweep_matcher):
        solutions = sweep_matcher.calculate()
        l1, l2 = solutions[0]
        result = frequency_sweep(
            sweep_matcher, l1, l2,
            center_freq=1e9, freq_start=0.5e9, freq_stop=1.5e9,
            num_points=51,
        )
        assert np.all(result.vswr >= 1.0)

    def test_gamma_magnitude_bounded(self, sweep_matcher):
        solutions = sweep_matcher.calculate()
        l1, l2 = solutions[0]
        result = frequency_sweep(
            sweep_matcher, l1, l2,
            center_freq=1e9, freq_start=0.5e9, freq_stop=1.5e9,
            num_points=51,
        )
        assert np.all(result.reflection_coefficient >= 0)
        assert np.all(result.reflection_coefficient <= 1)

    def test_attributes_populated(self, sweep_matcher):
        solutions = sweep_matcher.calculate()
        l1, l2 = solutions[0]
        result = frequency_sweep(
            sweep_matcher, l1, l2,
            center_freq=1e9, freq_start=0.5e9, freq_stop=1.5e9,
        )
        assert result.center_frequency == 1e9
        assert result.l1_wavelengths_center == l1
        assert result.l2_wavelengths_center == l2
        assert result.reflection_coefficient_complex is not None


class TestFrequencySweepVectorised:
    def test_sweep_nan_safety(self):
        """Sweep with a near-singular load should not produce NaN."""
        matcher = DoubleStubMatcher(
            distance_to_first_stub=0.0,
            distance_between_stubs=0.5,
            load_impedance=complex(0.01, 0),
            line_impedance=50.0,
            stub_impedance=50.0,
        )
        # Use arbitrary stub lengths (not valid solutions)
        result = frequency_sweep(
            matcher, 0.1, 0.2,
            center_freq=1e9, freq_start=0.5e9, freq_stop=1.5e9,
            num_points=51,
        )
        assert not np.any(np.isnan(result.reflection_coefficient))

    def test_large_sweep_performance(self, sweep_matcher):
        """10001-point sweep should produce correct results."""
        solutions = sweep_matcher.calculate()
        l1, l2 = solutions[0]
        result = frequency_sweep(
            sweep_matcher, l1, l2,
            center_freq=1e9, freq_start=0.5e9, freq_stop=1.5e9,
            num_points=10001,
        )
        assert len(result.frequencies) == 10001
        assert np.all(result.reflection_coefficient >= 0)
        assert np.all(result.reflection_coefficient <= 1.0001)  # small tolerance


class TestBandwidthMetrics:
    def test_bandwidth_3db_positive(self, sweep_matcher):
        solutions = sweep_matcher.calculate()
        l1, l2 = solutions[0]
        sr = frequency_sweep(
            sweep_matcher, l1, l2,
            center_freq=1e9, freq_start=0.5e9, freq_stop=1.5e9,
            num_points=201,
        )
        assert sr.bandwidth_3db > 0

    def test_bandwidth_10db_le_3db(self, sweep_matcher):
        solutions = sweep_matcher.calculate()
        l1, l2 = solutions[0]
        sr = frequency_sweep(
            sweep_matcher, l1, l2,
            center_freq=1e9, freq_start=0.5e9, freq_stop=1.5e9,
            num_points=201,
        )
        assert sr.bandwidth_10db_rl <= sr.bandwidth_3db

    def test_fractional_bandwidth_range(self, sweep_matcher):
        solutions = sweep_matcher.calculate()
        l1, l2 = solutions[0]
        sr = frequency_sweep(
            sweep_matcher, l1, l2,
            center_freq=1e9, freq_start=0.5e9, freq_stop=1.5e9,
            num_points=201,
        )
        assert 0 < sr.fractional_bandwidth < 200

    def test_q_factor_positive(self, sweep_matcher):
        solutions = sweep_matcher.calculate()
        l1, l2 = solutions[0]
        sr = frequency_sweep(
            sweep_matcher, l1, l2,
            center_freq=1e9, freq_start=0.5e9, freq_stop=1.5e9,
            num_points=201,
        )
        assert sr.q_factor > 0

    def test_phase_deg_shape(self, sweep_matcher):
        solutions = sweep_matcher.calculate()
        l1, l2 = solutions[0]
        N = 51
        sr = frequency_sweep(
            sweep_matcher, l1, l2,
            center_freq=1e9, freq_start=0.5e9, freq_stop=1.5e9,
            num_points=N,
        )
        assert sr.phase_deg.shape == (N,)

    def test_group_delay_no_nan(self, sweep_matcher):
        solutions = sweep_matcher.calculate()
        l1, l2 = solutions[0]
        sr = frequency_sweep(
            sweep_matcher, l1, l2,
            center_freq=1e9, freq_start=0.5e9, freq_stop=1.5e9,
            num_points=51,
        )
        assert not np.any(np.isnan(sr.group_delay_ns))

    def test_zero_bandwidth_no_crash(self):
        """Badly mismatched stubs should give zero bandwidth, not crash."""
        matcher = DoubleStubMatcher(
            distance_to_first_stub=0.0,
            distance_between_stubs=0.5,
            load_impedance=complex(0.01, 0),
            line_impedance=50.0,
            stub_impedance=50.0,
        )
        sr = frequency_sweep(
            matcher, 0.1, 0.2,
            center_freq=1e9, freq_start=0.5e9, freq_stop=1.5e9,
            num_points=51,
        )
        # Should not crash; bandwidth may be zero
        assert sr.bandwidth_3db >= 0
        assert sr.bandwidth_10db_rl >= 0


class TestRankSolutions:
    def test_rank_returns_sorted(self, sweep_matcher):
        from double_stub.frequency_sweep import rank_solutions
        solutions = sweep_matcher.calculate()
        assert len(solutions) >= 2, "Need multiple solutions to test ranking"
        rankings = rank_solutions(
            sweep_matcher, solutions,
            center_freq=1e9, freq_start=0.5e9, freq_stop=1.5e9,
            num_points=51,
        )
        assert len(rankings) == len(solutions)
        # Should be sorted descending by bandwidth_10db_rl
        for i in range(len(rankings) - 1):
            assert rankings[i]['bandwidth_10db_rl'] >= rankings[i + 1]['bandwidth_10db_rl']

    def test_rank_has_expected_fields(self, sweep_matcher):
        from double_stub.frequency_sweep import rank_solutions
        solutions = sweep_matcher.calculate()
        rankings = rank_solutions(
            sweep_matcher, solutions,
            center_freq=1e9, freq_start=0.5e9, freq_stop=1.5e9,
            num_points=51,
        )
        expected_keys = {'solution_index', 'l1', 'l2', 'sweep',
                         'bandwidth_3db', 'bandwidth_10db_rl',
                         'bandwidth_vswr2', 'fractional_bandwidth', 'q_factor'}
        for r in rankings:
            assert expected_keys.issubset(r.keys())


class TestFrequencySweepCLI:
    def test_freq_sweep_requires_center_freq(self):
        from double_stub.cli import main
        result = main(['--freq-sweep', '0.5e9,1.5e9,11'])
        assert result == 1

    def test_freq_sweep_invalid_format(self):
        from double_stub.cli import main
        result = main(['--freq-sweep', 'bad', '--center-freq', '1e9'])
        assert result == 1

    def test_freq_sweep_runs_successfully(self, capsys):
        from double_stub.cli import main
        result = main([
            '--freq-sweep', '0.5e9,1.5e9,11',
            '--center-freq', '1e9',
        ])
        captured = capsys.readouterr()
        assert 'Freq (Hz)' in captured.out
        assert result == 0

    def test_freq_sweep_all_solutions(self, capsys):
        """Without --solution-index, all solutions should be swept."""
        from double_stub.cli import main
        result = main([
            '--freq-sweep', '0.5e9,1.5e9,5',
            '--center-freq', '1e9',
        ])
        captured = capsys.readouterr()
        assert result == 0
        # Should contain at least two tables (Solution 1, Solution 2)
        assert 'Solution 1' in captured.out
        assert 'Solution 2' in captured.out

    def test_solution_index_flag(self, capsys):
        """--solution-index=1 should sweep only solution 1."""
        from double_stub.cli import main
        result = main([
            '--freq-sweep', '0.5e9,1.5e9,5',
            '--center-freq', '1e9',
            '--solution-index', '1',
        ])
        captured = capsys.readouterr()
        assert result == 0
        assert 'Freq (Hz)' in captured.out
        # Only one table should appear (count occurrences of header line)
        assert captured.out.count('Freq (Hz)') == 1
