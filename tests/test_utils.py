"""Tests for utility functions."""

import math

import numpy as np
import pytest

from double_stub.utils import (
    cot,
    parse_complex_impedance,
    remove_duplicate_pairs,
    remove_duplicate_solutions,
)


class TestCot:
    def test_cot_pi_over_4(self):
        assert abs(cot(math.pi / 4) - 1.0) < 1e-10

    def test_cot_pi_over_2(self):
        assert abs(cot(math.pi / 2)) < 1e-10

    def test_cot_singularity_at_zero(self):
        result = cot(0.0)
        assert math.isinf(result)
        assert result > 0

    def test_cot_singularity_at_pi(self):
        result = cot(math.pi)
        assert math.isinf(result)
        assert result < 0

    def test_cot_ndarray(self):
        x = np.array([math.pi / 4, math.pi / 2])
        result = cot(x)
        assert abs(result[0] - 1.0) < 1e-10
        assert abs(result[1]) < 1e-10


class TestParseComplexImpedance:
    def test_valid_impedance(self):
        result = parse_complex_impedance("38.9,-26.7")
        assert result == complex(38.9, -26.7)

    def test_positive_imaginary(self):
        result = parse_complex_impedance("100,50")
        assert result == complex(100, 50)

    def test_invalid_format_no_comma(self):
        with pytest.raises(ValueError):
            parse_complex_impedance("38.9")

    def test_invalid_format_non_numeric(self):
        with pytest.raises(ValueError):
            parse_complex_impedance("abc,def")

    def test_too_many_parts(self):
        with pytest.raises(ValueError):
            parse_complex_impedance("1,2,3")

    def test_parse_with_spaces(self):
        result = parse_complex_impedance("  38.9 , -26.7  ")
        assert result == complex(38.9, -26.7)

    def test_parse_j_format_positive(self):
        result = parse_complex_impedance("38.9+j26.7")
        assert result == complex(38.9, 26.7)

    def test_parse_j_format_negative(self):
        result = parse_complex_impedance("38.9-j26.7")
        assert result == complex(38.9, -26.7)

    def test_parse_j_format_no_sign(self):
        # Without explicit +/- before j, should fail since format expects R+jX
        with pytest.raises(ValueError):
            parse_complex_impedance("38.9j26.7")

    def test_parse_scientific_notation_real(self):
        result = parse_complex_impedance("1e2+j50")
        assert abs(result.real - 100.0) < 1e-10
        assert abs(result.imag - 50.0) < 1e-10

    def test_parse_scientific_notation_imag(self):
        result = parse_complex_impedance("38.9-j2.67e1")
        assert abs(result.real - 38.9) < 1e-10
        assert abs(result.imag - (-26.7)) < 1e-10

    def test_parse_scientific_notation_both(self):
        result = parse_complex_impedance("1e2+j5e1")
        assert abs(result.real - 100.0) < 1e-10
        assert abs(result.imag - 50.0) < 1e-10


class TestRemoveDuplicateSolutions:
    def test_no_duplicates(self):
        result = remove_duplicate_solutions([0.1, 0.2, 0.3], 1e-6)
        assert len(result) == 3

    def test_with_duplicates(self):
        result = remove_duplicate_solutions([0.1, 0.1 + 1e-10, 0.2], 1e-6)
        assert len(result) == 2

    def test_empty_list(self):
        result = remove_duplicate_solutions([], 1e-6)
        assert result == []

    def test_all_same(self):
        result = remove_duplicate_solutions([0.5, 0.5, 0.5], 1e-6)
        assert len(result) == 1


class TestRemoveDuplicatePairs:
    def test_no_duplicates(self):
        pairs = [(0.1, 0.2), (0.3, 0.4)]
        result = remove_duplicate_pairs(pairs, 1e-6)
        assert len(result) == 2

    def test_with_duplicates(self):
        pairs = [(0.1, 0.2), (0.1 + 1e-10, 0.2 + 1e-10), (0.3, 0.4)]
        result = remove_duplicate_pairs(pairs, 1e-6)
        assert len(result) == 2

    def test_empty(self):
        result = remove_duplicate_pairs([], 1e-6)
        assert result == []

    def test_different_l1_same_l2(self):
        pairs = [(0.1, 0.3), (0.2, 0.3)]
        result = remove_duplicate_pairs(pairs, 1e-6)
        assert len(result) == 2

    def test_same_l1_different_l2(self):
        pairs = [(0.1, 0.2), (0.1, 0.4)]
        result = remove_duplicate_pairs(pairs, 1e-6)
        assert len(result) == 2
