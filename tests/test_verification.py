"""Tests for solution verification."""

import math

from double_stub.core import DoubleStubMatcher


class TestVerification:
    def test_known_good_solution(self, default_matcher):
        solutions = default_matcher.calculate()
        assert len(solutions) > 0
        l1, l2 = solutions[0]
        result = default_matcher.verify_solution(l1, l2)
        assert result['valid']
        assert result['reflection_coefficient'] < 1e-4

    def test_random_pair_fails(self, default_matcher):
        result = default_matcher.verify_solution(0.123, 0.456)
        assert not result['valid']
        assert result['reflection_coefficient'] > 0.01

    def test_verify_returns_vswr(self, default_matcher):
        solutions = default_matcher.calculate()
        l1, l2 = solutions[0]
        result = default_matcher.verify_solution(l1, l2)
        assert 'vswr' in result
        assert 'return_loss_db' in result

    def test_vswr_formula_correctness(self, default_matcher):
        solutions = default_matcher.calculate()
        l1, l2 = solutions[0]
        result = default_matcher.verify_solution(l1, l2)
        gamma = result['reflection_coefficient']
        expected_vswr = (1 + gamma) / (1 - gamma)
        assert abs(result['vswr'] - expected_vswr) < 1e-10

    def test_return_loss_formula_correctness(self, default_matcher):
        solutions = default_matcher.calculate()
        l1, l2 = solutions[0]
        result = default_matcher.verify_solution(l1, l2)
        gamma = result['reflection_coefficient']
        expected_rl = -20 * math.log10(gamma) if gamma > 0 else float('inf')
        assert abs(result['return_loss_db'] - expected_rl) < 1e-6

    def test_vswr_always_ge_one(self, default_matcher):
        solutions = default_matcher.calculate()
        for l1, l2 in solutions:
            result = default_matcher.verify_solution(l1, l2)
            assert result['vswr'] >= 1.0
