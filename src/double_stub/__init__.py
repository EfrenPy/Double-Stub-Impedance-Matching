"""
Double-Stub Impedance Matching Calculator.

A Python tool for calculating double-stub impedance matching solutions
in transmission line systems.
"""

__version__ = "2.5.1"

from .constants import (
    DEFAULT_DISTANCE_BETWEEN_STUBS,
    DEFAULT_DISTANCE_TO_FIRST_STUB,
    DEFAULT_LINE_IMPEDANCE,
    DEFAULT_LOAD_IMPEDANCE,
    DEFAULT_MAX_LENGTH,
    DEFAULT_PRECISION,
    DEFAULT_STUB_IMPEDANCE,
    DEFAULT_STUB_TOPOLOGY,
    DEFAULT_STUB_TYPE,
)
from .core import DoubleStubMatcher, VerificationResult
from .frequency_sweep import FrequencySweepResult, frequency_sweep, rank_solutions
from .utils import (
    cot,
    parse_complex_impedance,
    remove_duplicate_pairs,
    remove_duplicate_solutions,
)

__all__ = [
    'DoubleStubMatcher',
    'VerificationResult',
    'FrequencySweepResult',
    'frequency_sweep',
    'rank_solutions',
    'cot',
    'parse_complex_impedance',
    'remove_duplicate_solutions',
    'remove_duplicate_pairs',
    'DEFAULT_DISTANCE_TO_FIRST_STUB',
    'DEFAULT_DISTANCE_BETWEEN_STUBS',
    'DEFAULT_LOAD_IMPEDANCE',
    'DEFAULT_LINE_IMPEDANCE',
    'DEFAULT_STUB_IMPEDANCE',
    'DEFAULT_STUB_TYPE',
    'DEFAULT_STUB_TOPOLOGY',
    'DEFAULT_PRECISION',
    'DEFAULT_MAX_LENGTH',
]
