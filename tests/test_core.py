"""Tests for the core calculation engine."""

import warnings

import numpy as np
import pytest

from double_stub.core import DoubleStubMatcher


class TestDoubleStubMatcher:
    def test_default_finds_two_solutions(self, default_matcher):
        solutions = default_matcher.calculate()
        assert len(solutions) == 2

    def test_solutions_are_verified(self, default_matcher):
        solutions = default_matcher.calculate()
        for l1, l2 in solutions:
            result = default_matcher.verify_solution(l1, l2)
            assert result['valid'], (
                f"Solution l1={l1}, l2={l2} failed verification: "
                f"|Gamma|={result['reflection_coefficient']}"
            )

    def test_resistive_load(self):
        matcher = DoubleStubMatcher(
            distance_to_first_stub=0.07,
            distance_between_stubs=3.0 / 8.0,
            load_impedance=complex(100, 0),
            line_impedance=50.0,
            stub_impedance=50.0,
        )
        solutions = matcher.calculate()
        assert len(solutions) > 0

    def test_open_stub(self):
        matcher = DoubleStubMatcher(
            distance_to_first_stub=0.07,
            distance_between_stubs=3.0 / 8.0,
            load_impedance=complex(38.9, -26.7),
            line_impedance=50.0,
            stub_impedance=50.0,
            stub_type='open',
        )
        solutions = matcher.calculate()
        assert len(solutions) > 0
        for l1, l2 in solutions:
            result = matcher.verify_solution(l1, l2)
            assert result['valid']

    def test_transform_admittance_zero_distance(self, default_matcher):
        y = complex(0.02, -0.01)
        result = default_matcher.transform_admittance(y, 0)
        assert abs(result - y) < 1e-10

    def test_stub_admittance_quarter_wave_short(self):
        matcher = DoubleStubMatcher(
            distance_to_first_stub=0.07,
            distance_between_stubs=3.0 / 8.0,
            load_impedance=complex(50, 0),
            line_impedance=50.0,
            stub_impedance=50.0,
            stub_type='short',
        )
        # Quarter wave = 0.25 wavelengths; short stub -> Y = -jY0*cot(pi/2) ~ 0
        y = matcher.stub_admittance(0.25)
        assert abs(y) < 1e-10

    def test_stub_admittance_quarter_wave_open(self):
        matcher = DoubleStubMatcher(
            distance_to_first_stub=0.07,
            distance_between_stubs=3.0 / 8.0,
            load_impedance=complex(50, 0),
            line_impedance=50.0,
            stub_impedance=50.0,
            stub_type='open',
        )
        # Quarter wave open stub: Y = jY0*tan(pi/2) -> large magnitude
        y = matcher.stub_admittance(0.25)
        assert abs(y) > 1e6

    def test_max_length_parameter(self):
        matcher = DoubleStubMatcher(
            distance_to_first_stub=0.07,
            distance_between_stubs=3.0 / 8.0,
            load_impedance=complex(38.9, -26.7),
            line_impedance=50.0,
            stub_impedance=50.0,
            max_length=1.0,
        )
        solutions = matcher.calculate()
        assert len(solutions) >= 2
        for l1, l2 in solutions:
            assert 0 < l1 < 1.0
            assert 0 < l2 < 1.0

    def test_series_topology(self):
        matcher = DoubleStubMatcher(
            distance_to_first_stub=0.07,
            distance_between_stubs=3.0 / 8.0,
            load_impedance=complex(38.9, -26.7),
            line_impedance=50.0,
            stub_impedance=50.0,
            stub_topology='series',
        )
        solutions = matcher.calculate()
        assert len(solutions) > 0
        for l1, l2 in solutions:
            result = matcher.verify_solution(l1, l2)
            assert result['valid'], (
                f"Series solution l1={l1}, l2={l2} failed: "
                f"|Gamma|={result['reflection_coefficient']}"
            )

    def test_invalid_stub_type_rejected(self):
        with pytest.raises(ValueError):
            DoubleStubMatcher(
                distance_to_first_stub=0.07,
                distance_between_stubs=3.0 / 8.0,
                load_impedance=complex(50, 0),
                line_impedance=50.0,
                stub_impedance=50.0,
                stub_type='invalid',
            )


class TestSolutionPairing:
    def test_solution_pairs_are_correctly_associated(self, default_matcher):
        """Each returned (l1, l2) pair should pass verification."""
        solutions = default_matcher.calculate()
        assert len(solutions) >= 2
        for l1, l2 in solutions:
            result = default_matcher.verify_solution(l1, l2)
            assert result['valid'], (
                f"Pair (l1={l1:.6f}, l2={l2:.6f}) failed: "
                f"|Gamma|={result['reflection_coefficient']:.6e}"
            )

    def test_all_pairs_pass_verification(self):
        """Test with different load to ensure pairing is correct."""
        matcher = DoubleStubMatcher(
            distance_to_first_stub=0.1,
            distance_between_stubs=0.25,
            load_impedance=complex(75, -30),
            line_impedance=50.0,
            stub_impedance=50.0,
        )
        solutions = matcher.calculate()
        for l1, l2 in solutions:
            result = matcher.verify_solution(l1, l2)
            assert result['valid']


class TestForbiddenRegion:
    def test_forbidden_region_detected(self):
        """Low-Z load with d=lambda/4 should trigger forbidden region."""
        matcher = DoubleStubMatcher(
            distance_to_first_stub=0.0,
            distance_between_stubs=0.25,
            load_impedance=complex(10, 0),
            line_impedance=50.0,
            stub_impedance=50.0,
        )
        result = matcher.check_forbidden_region()
        assert result['in_forbidden_region']
        assert 'forbidden region' in result['message'].lower()

    def test_forbidden_region_not_triggered(self, default_matcher):
        """Default parameters should not be in forbidden region."""
        result = default_matcher.check_forbidden_region()
        assert not result['in_forbidden_region']
        assert result['message'] == ''

    def test_forbidden_region_series_topology(self):
        """Series topology forbidden region detection."""
        matcher = DoubleStubMatcher(
            distance_to_first_stub=0.0,
            distance_between_stubs=0.25,
            load_impedance=complex(200, 0),
            line_impedance=50.0,
            stub_impedance=50.0,
            stub_topology='series',
        )
        result = matcher.check_forbidden_region()
        # High-Z load with series topology at d=lambda/4
        assert result['in_forbidden_region']


class TestDeduplication:
    def test_no_duplicate_verified_solutions(self, default_matcher):
        """No two returned solutions should have the same (l1, l2) pair."""
        solutions = default_matcher.calculate()
        for i in range(len(solutions)):
            for j in range(i + 1, len(solutions)):
                l1_diff = abs(solutions[i][0] - solutions[j][0])
                l2_diff = abs(solutions[i][1] - solutions[j][1])
                assert l1_diff > 1e-6 or l2_diff > 1e-6, (
                    f"Duplicate pair: solutions {i} and {j} are "
                    f"({solutions[i]}) and ({solutions[j]})"
                )

    def test_all_returned_solutions_are_verified(self, default_matcher):
        """All returned solutions should pass verification."""
        solutions = default_matcher.calculate()
        for l1, l2 in solutions:
            vr = default_matcher.verify_solution(l1, l2)
            assert vr['valid']


class TestRuntimeWarnings:
    def test_no_runtime_warnings_during_solve(self, default_matcher):
        """Solver should not emit RuntimeWarnings."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            default_matcher.calculate()
            runtime_warnings = [
                x for x in w if issubclass(x.category, RuntimeWarning)
            ]
            assert len(runtime_warnings) == 0, (
                f"Got {len(runtime_warnings)} RuntimeWarning(s): "
                f"{[str(x.message) for x in runtime_warnings]}"
            )


class TestSmartGuesses:
    def test_smart_guesses_finds_all_solutions(self):
        """Smart guesses should find at least as many solutions as brute force."""
        matcher = DoubleStubMatcher(
            distance_to_first_stub=0.07,
            distance_between_stubs=3.0 / 8.0,
            load_impedance=complex(38.9, -26.7),
            line_impedance=50.0,
            stub_impedance=50.0,
        )
        solutions = matcher.calculate()
        assert len(solutions) >= 2
        for l1, l2 in solutions:
            result = matcher.verify_solution(l1, l2)
            assert result['valid']

    def test_reduced_trials_still_finds_solutions(self):
        """With num_trials=50, solver should still find all solutions."""
        matcher = DoubleStubMatcher(
            distance_to_first_stub=0.07,
            distance_between_stubs=3.0 / 8.0,
            load_impedance=complex(38.9, -26.7),
            line_impedance=50.0,
            stub_impedance=50.0,
        )
        l1_solutions = matcher.find_first_stub_solutions(num_trials=50)
        assert len(l1_solutions) >= 2
        pairs = matcher.find_second_stub_solutions(l1_solutions, num_trials=50)
        assert len(pairs) >= 2
        for l1, l2 in pairs:
            result = matcher.verify_solution(l1, l2)
            assert result['valid']

    def test_analytical_stub2_accuracy(self):
        """Analytical stub 2 solutions should pass verification."""
        matcher = DoubleStubMatcher(
            distance_to_first_stub=0.07,
            distance_between_stubs=3.0 / 8.0,
            load_impedance=complex(38.9, -26.7),
            line_impedance=50.0,
            stub_impedance=50.0,
        )
        l1_solutions = matcher.find_first_stub_solutions()
        assert len(l1_solutions) > 0
        for l1 in l1_solutions:
            analytical = matcher._solve_stub2_analytically(l1)
            for l2 in analytical:
                result = matcher.verify_solution(l1, l2)
                assert result['valid'], (
                    f"Analytical l2={l2:.6f} for l1={l1:.6f} failed: "
                    f"|Gamma|={result['reflection_coefficient']:.6e}"
                )
