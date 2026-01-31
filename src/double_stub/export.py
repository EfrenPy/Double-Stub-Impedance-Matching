"""Export functions for double-stub matching results."""

from __future__ import annotations

import csv
import io
import json
import math
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from .frequency_sweep import FrequencySweepResult


def _json_safe_float(value: float) -> Optional[float]:
    """Return None for inf/NaN values, otherwise the float itself."""
    if math.isinf(value) or math.isnan(value):
        return None
    return value


def format_text(solutions: List[Tuple[float, float]],
                config: Dict[str, Any],
                verification_results: Optional[List[Dict[str, Any]]] = None) -> str:
    """
    Format solutions as human-readable text.

    Parameters
    ----------
    solutions : list of tuples
        List of (l1, l2) stub length pairs in wavelengths
    config : dict
        Configuration parameters used for the calculation
    verification_results : list of dict, optional
        Verification results for each solution

    Returns
    -------
    str
        Formatted text output
    """
    lines = []
    lines.append("=" * 60)
    lines.append("Double-Stub Impedance Matching Calculator")
    lines.append("=" * 60)
    lines.append(f"Load impedance:              {config['load_impedance']:.2f} \u03a9")
    lines.append(f"Line impedance:              {config['line_impedance']:.2f} \u03a9")
    lines.append(f"Stub impedance:              {config['stub_impedance']:.2f} \u03a9")
    lines.append(f"Stub type:                   {config['stub_type']}-circuited")
    lines.append(f"Stub topology:               {config.get('stub_topology', 'shunt')}")
    lines.append(f"Distance to first stub:      {config['distance_to_first_stub']:.4f} \u03bb")
    lines.append(f"Distance between stubs:      {config['distance_between_stubs']:.4f} \u03bb")
    lines.append(f"Numerical precision:         {config['precision']}")
    lines.append("=" * 60)

    if len(solutions) == 0:
        lines.append("")
        lines.append("No valid solutions found!")
        lines.append("This may occur if the load is outside the matchable region.")
    else:
        lines.append(f"\nFound {len(solutions)} matching solution(s):\n")

        for i, (l1, l2) in enumerate(solutions, 1):
            lines.append(f"Solution {i}:")
            lines.append(f"  First stub length (l1):   {l1:.6f} \u03bb  ({l1*360:.2f}\u00b0)")
            lines.append(f"  Second stub length (l2):  {l2:.6f} \u03bb  ({l2*360:.2f}\u00b0)")
            if verification_results and i <= len(verification_results):
                vr = verification_results[i - 1]
                status = "PASS" if vr['valid'] else "FAIL"
                lines.append(f"  Verification:             {status} "
                             f"(|\u0393| = {vr['reflection_coefficient']:.6f})")
                if 'vswr' in vr:
                    vswr = vr['vswr']
                    vswr_str = f"{vswr:.3f}" if vswr != float('inf') else "inf"
                    lines.append(f"  VSWR:                     {vswr_str}")
                if 'return_loss_db' in vr:
                    rl = vr['return_loss_db']
                    rl_str = f"{rl:.2f} dB" if rl != float('inf') else "inf dB"
                    lines.append(f"  Return Loss:              {rl_str}")
            lines.append("")

    return "\n".join(lines)


def format_json(solutions: List[Tuple[float, float]],
                config: Dict[str, Any],
                verification_results: Optional[List[Dict[str, Any]]] = None) -> str:
    """
    Format solutions as JSON.

    Parameters
    ----------
    solutions : list of tuples
        List of (l1, l2) stub length pairs in wavelengths
    config : dict
        Configuration parameters used for the calculation
    verification_results : list of dict, optional
        Verification results for each solution

    Returns
    -------
    str
        JSON string
    """
    # Make config JSON-serializable
    json_config = {}
    for key, value in config.items():
        if isinstance(value, complex):
            json_config[key] = {'real': value.real, 'imag': value.imag}
        else:
            json_config[key] = value

    json_solutions = []
    for i, (l1, l2) in enumerate(solutions):
        sol: Dict[str, Any] = {
            'solution_number': i + 1,
            'l1_wavelengths': float(l1),
            'l2_wavelengths': float(l2),
            'l1_degrees': float(l1 * 360),
            'l2_degrees': float(l2 * 360),
        }
        if verification_results and i < len(verification_results):
            vr = verification_results[i]
            verification_dict: Dict[str, Any] = {
                'valid': bool(vr['valid']),
                'reflection_coefficient': float(vr['reflection_coefficient']),
                'error': float(vr['error']),
            }
            if 'vswr' in vr:
                verification_dict['vswr'] = _json_safe_float(float(vr['vswr']))
            if 'return_loss_db' in vr:
                verification_dict['return_loss_db'] = _json_safe_float(float(vr['return_loss_db']))
            sol['verification'] = verification_dict
        json_solutions.append(sol)

    output = {
        'config': json_config,
        'solutions': json_solutions,
    }

    return json.dumps(output, indent=2)


def format_csv(solutions: List[Tuple[float, float]],
               config: Dict[str, Any],
               verification_results: Optional[List[Dict[str, Any]]] = None) -> str:
    """
    Format solutions as CSV.

    Parameters
    ----------
    solutions : list of tuples
        List of (l1, l2) stub length pairs in wavelengths
    config : dict
        Configuration parameters used for the calculation
    verification_results : list of dict, optional
        Verification results for each solution

    Returns
    -------
    str
        CSV string
    """
    output = io.StringIO()
    writer = csv.writer(output)

    has_verification = verification_results is not None and len(verification_results) > 0
    has_vswr = (has_verification
                and verification_results is not None
                and 'vswr' in verification_results[0])

    header = ['solution', 'l1_wavelengths', 'l2_wavelengths',
              'l1_degrees', 'l2_degrees']
    if has_vswr:
        header.extend(['vswr', 'return_loss_db'])
    writer.writerow(header)

    for i, (l1, l2) in enumerate(solutions, 1):
        row = [i, f"{l1:.6f}", f"{l2:.6f}",
               f"{l1*360:.2f}", f"{l2*360:.2f}"]
        if has_vswr and verification_results is not None and i <= len(verification_results):
            vr = verification_results[i - 1]
            vswr_val = vr['vswr']
            rl_val = vr['return_loss_db']
            row.append(f"{vswr_val:.6f}" if math.isfinite(vswr_val) else "")
            row.append(f"{rl_val:.2f}" if math.isfinite(rl_val) else "")
        writer.writerow(row)

    return output.getvalue()


def format_touchstone(sweep_result: FrequencySweepResult,
                      z0: float = 50.0, freq_unit: str = 'GHz',
                      format_type: str = 'MA') -> str:
    """
    Format frequency sweep results as a Touchstone (.s1p) file.

    Parameters
    ----------
    sweep_result : FrequencySweepResult
        Results from a frequency sweep
    z0 : float, optional
        Reference impedance (default 50.0)
    freq_unit : str, optional
        Frequency unit: 'Hz', 'kHz', 'MHz', 'GHz' (default 'GHz')
    format_type : str, optional
        Data format: 'MA' (magnitude/angle), 'DB' (dB/angle),
        'RI' (real/imaginary) (default 'MA')

    Returns
    -------
    str
        Touchstone .s1p formatted string
    """
    _FREQ_UNIT_CANONICAL = {'hz': 'Hz', 'khz': 'kHz', 'mhz': 'MHz', 'ghz': 'GHz'}
    freq_unit_lower = freq_unit.lower()
    freq_unit_display = _FREQ_UNIT_CANONICAL.get(freq_unit_lower, freq_unit)
    format_type = format_type.upper()

    freq_divisors = {'hz': 1.0, 'khz': 1e3, 'mhz': 1e6, 'ghz': 1e9}
    divisor = freq_divisors.get(freq_unit_lower, 1e9)

    lines = []
    lines.append("! Touchstone file generated by double-stub calculator")
    lines.append(f"! Center frequency: {sweep_result.center_frequency:.1f} Hz")
    lines.append(f"! Stub 1: {sweep_result.l1_wavelengths_center:.6f} wavelengths")
    lines.append(f"! Stub 2: {sweep_result.l2_wavelengths_center:.6f} wavelengths")
    lines.append(f"# {freq_unit_display} S {format_type} R {z0:.1f}")

    gamma_c = sweep_result.reflection_coefficient_complex
    freqs = sweep_result.frequencies

    for i in range(len(freqs)):
        freq_scaled = freqs[i] / divisor
        g = gamma_c[i]
        if not np.isfinite(g):
            g = complex(1.0, 0.0)

        if format_type == 'MA':
            val1 = abs(g)
            val2 = math.degrees(np.angle(g))
        elif format_type == 'DB':
            mag = abs(g)
            val1 = 20 * math.log10(mag) if mag > 0 else -999.0
            val2 = math.degrees(np.angle(g))
        elif format_type == 'RI':
            val1 = g.real
            val2 = g.imag
        else:
            raise ValueError(f"Unknown format type: {format_type}")

        lines.append(f"{freq_scaled:.9f}\t{val1:.9f}\t{val2:.9f}")

    return "\n".join(lines) + "\n"
