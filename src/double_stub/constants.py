"""Default configuration constants for the double-stub impedance matching calculator."""

from typing import Final

DEFAULT_DISTANCE_TO_FIRST_STUB: Final[float] = 0.07
DEFAULT_DISTANCE_BETWEEN_STUBS: Final[float] = 3.0 / 8.0
DEFAULT_LOAD_IMPEDANCE: Final[str] = '38.9,-26.7'
DEFAULT_LINE_IMPEDANCE: Final[float] = 50.0
DEFAULT_STUB_IMPEDANCE: Final[float] = 50.0
DEFAULT_STUB_TYPE: Final[str] = 'short'
DEFAULT_STUB_TOPOLOGY: Final[str] = 'shunt'
DEFAULT_PRECISION: Final[float] = 1e-8
DEFAULT_MAX_LENGTH: Final[float] = 0.5
