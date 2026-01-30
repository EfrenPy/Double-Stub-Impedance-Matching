"""Shared test fixtures."""

import pytest

from double_stub.core import DoubleStubMatcher


@pytest.fixture
def default_matcher():
    """Default matcher with standard test parameters."""
    return DoubleStubMatcher(
        distance_to_first_stub=0.07,
        distance_between_stubs=3.0 / 8.0,
        load_impedance=complex(38.9, -26.7),
        line_impedance=50.0,
        stub_impedance=50.0,
        stub_type='short',
        precision=1e-8,
    )


@pytest.fixture
def matched_load_matcher():
    """Matcher where load is already matched (Z_L = Z0)."""
    return DoubleStubMatcher(
        distance_to_first_stub=0.07,
        distance_between_stubs=3.0 / 8.0,
        load_impedance=complex(50.0, 0.0),
        line_impedance=50.0,
        stub_impedance=50.0,
        stub_type='short',
        precision=1e-8,
    )
