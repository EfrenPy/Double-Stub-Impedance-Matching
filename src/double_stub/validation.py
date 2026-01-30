"""Input validation for the double-stub impedance matching calculator."""

import math


def validate_parameters(line_impedance: float, stub_impedance: float,
                        load_impedance: complex,
                        distance_to_first_stub: float,
                        distance_between_stubs: float,
                        precision: float, max_length: float,
                        stub_type: str, stub_topology: str) -> None:
    """
    Validate all input parameters for the double-stub matcher.

    Parameters
    ----------
    line_impedance : float
        Characteristic impedance of the transmission line (Ohms)
    stub_impedance : float
        Characteristic impedance of the stubs (Ohms)
    load_impedance : complex
        Complex load impedance (Ohms)
    distance_to_first_stub : float
        Distance from load to first stub in wavelengths
    distance_between_stubs : float
        Distance between the two stubs in wavelengths
    precision : float
        Numerical tolerance for solutions
    max_length : float
        Maximum stub length in wavelengths
    stub_type : str
        Type of stub: 'short' or 'open'
    stub_topology : str
        Stub topology: 'shunt' or 'series'

    Raises
    ------
    ValueError
        If any parameter is invalid.
    """
    if line_impedance <= 0:
        raise ValueError(f"Line impedance must be positive, got {line_impedance}")

    if stub_impedance <= 0:
        raise ValueError(f"Stub impedance must be positive, got {stub_impedance}")

    if math.isnan(load_impedance.real) or math.isnan(load_impedance.imag):
        raise ValueError("Load impedance contains NaN")
    if math.isinf(load_impedance.real) or math.isinf(load_impedance.imag):
        raise ValueError("Load impedance contains infinity")

    if load_impedance.real < 0:
        raise ValueError(
            f"Load impedance real part must be non-negative, got {load_impedance.real}"
        )

    if abs(load_impedance) == 0:
        raise ValueError("Load impedance cannot be zero")

    if distance_to_first_stub < 0:
        raise ValueError(
            f"Distance to first stub must be non-negative, got {distance_to_first_stub}"
        )

    if distance_between_stubs <= 0:
        raise ValueError(
            f"Distance between stubs must be positive, got {distance_between_stubs}"
        )

    if precision <= 0:
        raise ValueError(f"Precision must be positive, got {precision}")

    if max_length <= 0:
        raise ValueError(f"Max stub length must be positive, got {max_length}")

    if stub_type not in ('short', 'open'):
        raise ValueError(f"Stub type must be 'short' or 'open', got '{stub_type}'")

    if stub_topology not in ('shunt', 'series'):
        raise ValueError(
            f"Stub topology must be 'shunt' or 'series', got '{stub_topology}'"
        )
