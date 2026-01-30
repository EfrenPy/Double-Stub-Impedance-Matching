"""Frequency sweep analysis for double-stub impedance matching."""

from __future__ import annotations

from typing import Any, Dict, List, TYPE_CHECKING, Union

import numpy as np
from numpy.typing import NDArray

from .utils import cot

if TYPE_CHECKING:
    from .core import DoubleStubMatcher


class FrequencySweepResult:
    """Results from a frequency sweep analysis.

    Attributes
    ----------
    frequencies : ndarray
        Frequency points in Hz
    reflection_coefficient : ndarray
        Magnitude of reflection coefficient at each frequency
    reflection_coefficient_complex : ndarray
        Complex reflection coefficient at each frequency
    vswr : ndarray
        VSWR at each frequency
    return_loss_db : ndarray
        Return loss in dB at each frequency
    center_frequency : float
        Center (design) frequency in Hz
    l1_wavelengths_center : float
        First stub length in wavelengths at center frequency
    l2_wavelengths_center : float
        Second stub length in wavelengths at center frequency
    """

    def __init__(self, frequencies: Union[List[float], NDArray[np.floating]],
                 reflection_coefficient_complex: Union[List[complex], NDArray[np.complexfloating]],
                 center_frequency: float,
                 l1_wavelengths_center: float,
                 l2_wavelengths_center: float) -> None:
        self.frequencies = np.asarray(frequencies)
        self.reflection_coefficient_complex = np.asarray(reflection_coefficient_complex)
        self.reflection_coefficient = np.abs(self.reflection_coefficient_complex)
        self.center_frequency = center_frequency
        self.l1_wavelengths_center = l1_wavelengths_center
        self.l2_wavelengths_center = l2_wavelengths_center

        # Compute VSWR: clip |Gamma| to avoid division by zero
        gamma_mag = np.clip(self.reflection_coefficient, 0, 0.99999)
        self.vswr = (1 + gamma_mag) / (1 - gamma_mag)

        # Compute return loss: handle |Gamma|=0 case
        with np.errstate(divide='ignore'):
            self.return_loss_db = np.where(
                self.reflection_coefficient > 0,
                -20 * np.log10(self.reflection_coefficient),
                np.inf
            )

    @property
    def phase_deg(self) -> NDArray[np.floating]:
        """Unwrapped S11 phase in degrees."""
        if not hasattr(self, '_phase_deg'):
            self._phase_deg = np.degrees(np.unwrap(
                np.angle(self.reflection_coefficient_complex)))
        return self._phase_deg

    @property
    def group_delay_ns(self) -> NDArray[np.floating]:
        """Group delay in nanoseconds: -d(phase)/d(omega)."""
        if not hasattr(self, '_group_delay_ns'):
            phase_rad = np.radians(self.phase_deg)
            omega = 2 * np.pi * self.frequencies
            self._group_delay_ns = -np.gradient(phase_rad, omega) * 1e9
        return self._group_delay_ns

    def _compute_bandwidth(self, s11_threshold: float) -> float:
        """Find contiguous bandwidth around center where |S11| < threshold.

        Returns bandwidth in Hz, or 0.0 if threshold is never met.
        """
        mask = self.reflection_coefficient < s11_threshold
        if not np.any(mask):
            return 0.0

        center_idx = np.argmin(np.abs(self.frequencies - self.center_frequency))
        if not mask[center_idx]:
            return 0.0

        # Walk outward from center
        low = center_idx
        while low > 0 and mask[low - 1]:
            low -= 1
        high = center_idx
        while high < len(self.frequencies) - 1 and mask[high + 1]:
            high += 1

        return float(self.frequencies[high] - self.frequencies[low])

    @property
    def bandwidth_3db(self) -> float:
        """3 dB bandwidth (|S11| < 0.707) in Hz."""
        if not hasattr(self, '_bandwidth_3db'):
            self._bandwidth_3db = self._compute_bandwidth(0.707)
        return self._bandwidth_3db

    @property
    def bandwidth_10db_rl(self) -> float:
        """10 dB return-loss bandwidth (|S11| < 0.316) in Hz."""
        if not hasattr(self, '_bandwidth_10db_rl'):
            self._bandwidth_10db_rl = self._compute_bandwidth(0.316)
        return self._bandwidth_10db_rl

    @property
    def bandwidth_vswr2(self) -> float:
        """VSWR < 2 bandwidth (|S11| < 0.333) in Hz."""
        if not hasattr(self, '_bandwidth_vswr2'):
            self._bandwidth_vswr2 = self._compute_bandwidth(0.333)
        return self._bandwidth_vswr2

    @property
    def fractional_bandwidth(self) -> float:
        """Fractional bandwidth as percentage: bandwidth_3db / center_freq * 100."""
        if not hasattr(self, '_fractional_bandwidth'):
            if self.center_frequency > 0 and self.bandwidth_3db > 0:
                self._fractional_bandwidth = self.bandwidth_3db / self.center_frequency * 100
            else:
                self._fractional_bandwidth = 0.0
        return self._fractional_bandwidth

    @property
    def q_factor(self) -> float:
        """Loaded Q factor: center_freq / bandwidth_3db."""
        if not hasattr(self, '_q_factor'):
            if self.bandwidth_3db > 0:
                self._q_factor = self.center_frequency / self.bandwidth_3db
            else:
                self._q_factor = float('inf')
        return self._q_factor


def _transform_admittance(admittance: complex,
                          distance_wavelengths: 'Union[float, NDArray[np.floating]]',
                          y0: float) -> 'Union[complex, NDArray[np.complexfloating]]':
    """Transform admittance along a transmission line.

    Accepts scalar or array ``distance_wavelengths`` for vectorised sweeps.
    """
    beta_l = 2 * np.pi * distance_wavelengths
    y_norm = admittance / y0
    cos_bl = np.cos(beta_l)
    sin_bl = np.sin(beta_l)
    numerator = y_norm * cos_bl + 1j * sin_bl
    denominator = cos_bl + 1j * sin_bl * y_norm
    return y0 * numerator / denominator


def _transform_impedance(impedance: complex,
                         distance_wavelengths: 'Union[float, NDArray[np.floating]]',
                         z0: float) -> 'Union[complex, NDArray[np.complexfloating]]':
    """Transform impedance along a transmission line."""
    beta_l = 2 * np.pi * distance_wavelengths
    z_norm = impedance / z0
    cos_bl = np.cos(beta_l)
    sin_bl = np.sin(beta_l)
    numerator = z_norm * cos_bl + 1j * sin_bl
    denominator = cos_bl + 1j * sin_bl * z_norm
    return z0 * numerator / denominator


def _stub_admittance(length_wavelengths: 'Union[float, NDArray[np.floating]]',
                     y0_stub: float,
                     stub_type: str) -> 'Union[complex, NDArray[np.complexfloating]]':
    """Calculate shunt stub admittance (scalar or array lengths)."""
    beta_l = 2 * np.pi * length_wavelengths
    if stub_type == 'short':
        return -1j * y0_stub * cot(beta_l)
    else:
        return 1j * y0_stub * np.tan(beta_l)


def _stub_impedance_series(length_wavelengths: 'Union[float, NDArray[np.floating]]',
                           z0_stub: float,
                           stub_type: str) -> 'Union[complex, NDArray[np.complexfloating]]':
    """Calculate series stub impedance (scalar or array lengths)."""
    beta_l = 2 * np.pi * length_wavelengths
    if stub_type == 'short':
        return 1j * z0_stub * np.tan(beta_l)
    else:
        return -1j * z0_stub * cot(beta_l)


def frequency_sweep(matcher: DoubleStubMatcher, l1: float, l2: float,
                    center_freq: float, freq_start: float, freq_stop: float,
                    num_points: int = 101) -> FrequencySweepResult:
    """Perform a frequency sweep for a given solution pair.

    Physical stub lengths are fixed (designed at center_freq). At each
    frequency, all electrical lengths are scaled by freq/center_freq.

    Parameters
    ----------
    matcher : DoubleStubMatcher
        The matcher instance with configuration
    l1 : float
        First stub length in wavelengths (at center_freq)
    l2 : float
        Second stub length in wavelengths (at center_freq)
    center_freq : float
        Design (center) frequency in Hz
    freq_start : float
        Start frequency in Hz
    freq_stop : float
        Stop frequency in Hz
    num_points : int, optional
        Number of frequency points (default 101)

    Returns
    -------
    FrequencySweepResult
        Sweep results with frequency-dependent reflection data
    """
    frequencies = np.linspace(freq_start, freq_stop, num_points)

    z0 = matcher.Z0
    y0 = matcher.Y0
    z0_stub = matcher.Z0_stub
    y0_stub = matcher.Y0_stub
    stub_type = matcher.stub_type
    topology = matcher.stub_topology

    # Physical distances in wavelengths at center freq
    l_dist = matcher.l      # distance to first stub
    d_dist = matcher.d      # distance between stubs

    # Load
    z_load = matcher.Z_load
    y_load = matcher.Y_load

    # Vectorised: scale all electrical lengths as arrays
    scales = frequencies / center_freq
    l_dist_f = l_dist * scales
    d_dist_f = d_dist * scales
    l1_f = l1 * scales
    l2_f = l2 * scales

    with np.errstate(divide='ignore', invalid='ignore'):
        if topology == 'shunt':
            y_at_stub1 = _transform_admittance(y_load, l_dist_f, y0)
            y_after_stub1 = y_at_stub1 + _stub_admittance(l1_f, y0_stub, stub_type)
            y_at_stub2 = _transform_admittance(y_after_stub1, d_dist_f, y0)
            y_final = y_at_stub2 + _stub_admittance(l2_f, y0_stub, stub_type)
            z_in = 1.0 / y_final
        else:
            z_at_stub1 = _transform_impedance(z_load, l_dist_f, z0)
            z_after_stub1 = z_at_stub1 + _stub_impedance_series(l1_f, z0_stub, stub_type)
            z_at_stub2 = _transform_impedance(z_after_stub1, d_dist_f, z0)
            z_in = z_at_stub2 + _stub_impedance_series(l2_f, z0_stub, stub_type)

        gamma_complex = (z_in - z0) / (z_in + z0)

    # NaN safety: replace NaN with total reflection
    nan_mask = np.isnan(gamma_complex)
    gamma_complex = np.where(nan_mask, 1.0 + 0j, gamma_complex)

    return FrequencySweepResult(
        frequencies=frequencies,
        reflection_coefficient_complex=gamma_complex,
        center_frequency=center_freq,
        l1_wavelengths_center=l1,
        l2_wavelengths_center=l2,
    )


def rank_solutions(matcher: DoubleStubMatcher,
                   solutions: List[tuple],
                   center_freq: float,
                   freq_start: float,
                   freq_stop: float,
                   num_points: int = 101) -> List[Dict[str, Any]]:
    """Sweep each solution pair and rank by bandwidth.

    Parameters
    ----------
    matcher : DoubleStubMatcher
        The matcher instance
    solutions : list of tuple
        List of (l1, l2) pairs
    center_freq : float
        Center frequency in Hz
    freq_start : float
        Start frequency in Hz
    freq_stop : float
        Stop frequency in Hz
    num_points : int, optional
        Number of frequency points (default 101)

    Returns
    -------
    list of dict
        Solution rankings sorted by bandwidth_10db_rl descending
    """
    rankings: List[Dict[str, Any]] = []
    for idx, (l1, l2) in enumerate(solutions):
        sr = frequency_sweep(
            matcher, l1, l2,
            center_freq=center_freq,
            freq_start=freq_start,
            freq_stop=freq_stop,
            num_points=num_points,
        )
        rankings.append({
            'solution_index': idx + 1,
            'l1': l1,
            'l2': l2,
            'sweep': sr,
            'bandwidth_3db': sr.bandwidth_3db,
            'bandwidth_10db_rl': sr.bandwidth_10db_rl,
            'bandwidth_vswr2': sr.bandwidth_vswr2,
            'fractional_bandwidth': sr.fractional_bandwidth,
            'q_factor': sr.q_factor,
        })

    rankings.sort(key=lambda r: r['bandwidth_10db_rl'], reverse=True)
    return rankings


def format_sweep_table(sweep_result: FrequencySweepResult,
                       label: str = '') -> str:
    """Format frequency sweep results as a text table.

    Parameters
    ----------
    sweep_result : FrequencySweepResult
        The sweep results to format
    label : str, optional
        Optional heading label (e.g., "Solution 1")

    Returns
    -------
    str
        Formatted table string
    """
    lines = []
    if label:
        lines.append(label)
        lines.append("=" * len(label))
    lines.append(f"{'Freq (Hz)':>14s}  {'|S11|':>10s}  {'VSWR':>8s}  {'RL (dB)':>10s}")
    lines.append("-" * 48)

    for i in range(len(sweep_result.frequencies)):
        freq = sweep_result.frequencies[i]
        s11 = sweep_result.reflection_coefficient[i]
        vswr = sweep_result.vswr[i]
        rl = sweep_result.return_loss_db[i]
        rl_str = f"{rl:.2f}" if rl != float('inf') else "inf"
        lines.append(f"{freq:14.1f}  {s11:10.6f}  {vswr:8.4f}  {rl_str:>10s}")

    # Bandwidth summary
    lines.append("")
    bw_3db = sweep_result.bandwidth_3db
    bw_10db = sweep_result.bandwidth_10db_rl
    bw_vswr2 = sweep_result.bandwidth_vswr2
    frac_bw = sweep_result.fractional_bandwidth
    q = sweep_result.q_factor
    lines.append(f"  3 dB Bandwidth:      {bw_3db / 1e6:.2f} MHz")
    lines.append(f"  10 dB RL Bandwidth:  {bw_10db / 1e6:.2f} MHz")
    lines.append(f"  VSWR<2 Bandwidth:    {bw_vswr2 / 1e6:.2f} MHz")
    lines.append(f"  Fractional BW:       {frac_bw:.1f}%")
    q_str = f"{q:.1f}" if q != float('inf') else "inf"
    lines.append(f"  Loaded Q:            {q_str}")

    return "\n".join(lines)
