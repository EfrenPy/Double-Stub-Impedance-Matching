"""Utility functions for the double-stub impedance matching calculator."""

from math import copysign, inf
from typing import List, Tuple, Union

import numpy as np
from numpy.typing import NDArray


def cot(x: Union[float, NDArray[np.floating]]) -> Union[float, NDArray[np.floating]]:
    """
    Calculate cotangent with singularity guard.

    Parameters
    ----------
    x : float or ndarray
        Angle in radians

    Returns
    -------
    float or ndarray
        Cotangent of x. Returns +/-inf when sin(x) is near zero.
    """
    sin_x = np.sin(x)
    cos_x = np.cos(x)
    if np.isscalar(sin_x):
        if abs(sin_x) < 1e-15:
            return copysign(inf, cos_x)
        return cos_x / sin_x
    # ndarray path
    result = np.where(
        np.abs(sin_x) < 1e-15,
        np.copysign(np.inf, cos_x),
        cos_x / sin_x
    )
    return result


def parse_complex_impedance(impedance_str: str) -> complex:
    """
    Parse complex impedance from string format.

    Supports two formats:
    - Comma-separated: ``"real,imaginary"`` (e.g., ``"38.9,-26.7"``)
    - Engineering notation: ``"R+jX"`` or ``"R-jX"`` (e.g., ``"38.9-j26.7"``)

    Whitespace around values is tolerated.

    Parameters
    ----------
    impedance_str : str
        Impedance string in one of the supported formats

    Returns
    -------
    complex
        Complex impedance value

    Raises
    ------
    ValueError
        If the string format is invalid or values are not numeric.
    """
    import re

    s = impedance_str.strip()

    # Try comma-separated format first
    if ',' in s:
        parts = [p.strip() for p in s.split(',')]
        if len(parts) != 2:
            raise ValueError(
                "Impedance must be in format 'real,imaginary' or 'R+jX'"
            )
        try:
            return complex(float(parts[0]), float(parts[1]))
        except ValueError:
            raise ValueError(
                f"Invalid impedance values: '{parts[0]}' and "
                f"'{parts[1]}' must be numeric"
            )

    # Try R+jX / R-jX format
    m = re.match(
        r'^([+-]?\d*\.?\d+(?:[eE][+-]?\d+)?)\s*([+-])\s*[jJ]\s*(\d*\.?\d+(?:[eE][+-]?\d+)?)$', s
    )
    if m:
        real_part = float(m.group(1))
        sign = 1.0 if m.group(2) == '+' else -1.0
        imag_part = sign * float(m.group(3))
        return complex(real_part, imag_part)

    raise ValueError(
        "Impedance must be in format 'real,imaginary' or 'R+jX'"
    )


def remove_duplicate_solutions(solutions: List[float],
                               tolerance: float) -> List[float]:
    """
    Remove duplicate solutions within specified tolerance.

    Parameters
    ----------
    solutions : list
        List of numerical solutions
    tolerance : float
        Tolerance for considering solutions as duplicates

    Returns
    -------
    list
        List with duplicates removed
    """
    if len(solutions) == 0:
        return solutions

    unique_solutions: List[float] = []
    for sol in solutions:
        is_duplicate = False
        for unique_sol in unique_solutions:
            if np.abs(sol - unique_sol) < tolerance:
                is_duplicate = True
                break
        if not is_duplicate:
            unique_solutions.append(sol)

    return unique_solutions


def remove_duplicate_pairs(pairs: List[Tuple[float, float]],
                           tolerance: float) -> List[Tuple[float, float]]:
    """
    Remove duplicate (l1, l2) pairs within specified tolerance.

    Parameters
    ----------
    pairs : list of tuple
        List of (l1, l2) pairs
    tolerance : float
        Tolerance for considering pairs as duplicates

    Returns
    -------
    list of tuple
        List with duplicate pairs removed
    """
    if len(pairs) == 0:
        return pairs

    unique: List[Tuple[float, float]] = []
    for p in pairs:
        is_dup = False
        for u in unique:
            if abs(p[0] - u[0]) < tolerance and abs(p[1] - u[1]) < tolerance:
                is_dup = True
                break
        if not is_dup:
            unique.append(p)

    return unique
