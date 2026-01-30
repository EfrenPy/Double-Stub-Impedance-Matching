"""Smith chart and frequency response visualization for double-stub impedance matching."""

from __future__ import annotations

from typing import List, Optional, Tuple, Union, TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from .core import DoubleStubMatcher
    from .frequency_sweep import FrequencySweepResult


def plot_smith_chart(matcher: DoubleStubMatcher,
                     solutions: List[Tuple[float, float]],
                     output_file: Optional[str] = None) -> None:
    """
    Plot solutions on a Smith chart.

    Parameters
    ----------
    matcher : DoubleStubMatcher
        The matcher instance with configuration
    solutions : list of tuples
        List of (l1, l2) stub length pairs
    output_file : str, optional
        If provided, save the plot to this file instead of showing interactively

    Raises
    ------
    ImportError
        If matplotlib is not installed
    """
    try:
        import matplotlib.pyplot as plt
        from matplotlib.patches import Arc, Circle
    except ImportError:
        raise ImportError(
            "matplotlib is required for Smith chart visualization. "
            "Install it with: pip install matplotlib  "
            "or: pip install double-stub[plot]"
        )

    fig, ax = plt.subplots(1, 1, figsize=(8, 8))
    ax.set_aspect('equal')
    ax.set_xlim(-1.2, 1.2)
    ax.set_ylim(-1.2, 1.2)
    ax.set_title('Smith Chart - Double-Stub Matching')

    # Draw unit circle
    unit_circle = Circle((0, 0), 1, fill=False, color='black', linewidth=1.5)
    ax.add_patch(unit_circle)

    # Draw constant resistance circles
    r_values = [0, 0.2, 0.5, 1.0, 2.0, 5.0]
    for r in r_values:
        center_x = r / (1 + r)
        radius = 1 / (1 + r)
        circle = Circle((center_x, 0), radius, fill=False, color='gray',
                        linewidth=0.5, linestyle='--')
        ax.add_patch(circle)

    # Draw constant reactance arcs
    x_values = [0.2, 0.5, 1.0, 2.0, 5.0]
    for x in x_values:
        if x == 0:
            continue
        center_x = 1.0
        center_y = 1.0 / x
        radius = 1.0 / x

        # Calculate arc angles to clip to unit circle
        theta1 = np.degrees(np.arctan2(-center_y, -center_x + 1))
        theta2 = np.degrees(np.arctan2(0 - center_y, 1 - center_x))

        arc_pos = Arc((center_x, center_y), 2 * radius, 2 * radius,
                      angle=0, theta1=theta1, theta2=theta2,
                      color='gray', linewidth=0.5, linestyle='--')
        arc_neg = Arc((center_x, -center_y), 2 * radius, 2 * radius,
                      angle=0, theta1=-theta2, theta2=-theta1,
                      color='gray', linewidth=0.5, linestyle='--')
        ax.add_patch(arc_pos)
        ax.add_patch(arc_neg)

    # Center line
    ax.plot([-1, 1], [0, 0], color='gray', linewidth=0.5)

    def impedance_to_gamma(z, z0):
        """Convert impedance to reflection coefficient."""
        return (z - z0) / (z + z0)

    def admittance_to_gamma(y, y0):
        """Convert admittance to reflection coefficient."""
        z = 1.0 / y if abs(y) > 1e-15 else complex(1e15, 0)
        z0 = 1.0 / y0
        return (z - z0) / (z + z0)

    colors = ['blue', 'red', 'green', 'purple']

    for sol_idx, (l1, l2) in enumerate(solutions):
        color = colors[sol_idx % len(colors)]
        label = f'Solution {sol_idx + 1}'

        if matcher.stub_topology == 'shunt':
            # Trace admittance path
            points = []

            # 1. Load admittance
            gamma_load = admittance_to_gamma(matcher.Y_load, matcher.Y0)
            points.append(gamma_load)

            # 2. Transform to stub 1 location
            n_steps = 50
            for k in range(1, n_steps + 1):
                dist = matcher.l * k / n_steps
                y = matcher.transform_admittance(matcher.Y_load, dist)
                points.append(admittance_to_gamma(y, matcher.Y0))

            # 3. Add stub 1 (move along constant conductance circle)
            y_at_stub1 = matcher.transform_admittance(matcher.Y_load, matcher.l)
            stub1_points = []
            for k in range(n_steps + 1):
                frac = k / n_steps
                y = y_at_stub1 + matcher.stub_admittance(l1) * frac
                stub1_points.append(admittance_to_gamma(y, matcher.Y0))
            points.extend(stub1_points)

            # 4. Transform to stub 2 location
            y_after_stub1 = y_at_stub1 + matcher.stub_admittance(l1)
            for k in range(1, n_steps + 1):
                dist = matcher.d * k / n_steps
                y = matcher.transform_admittance(y_after_stub1, dist)
                points.append(admittance_to_gamma(y, matcher.Y0))

            # 5. Add stub 2
            y_at_stub2 = matcher.transform_admittance(y_after_stub1, matcher.d)
            for k in range(n_steps + 1):
                frac = k / n_steps
                y = y_at_stub2 + matcher.stub_admittance(l2) * frac
                points.append(admittance_to_gamma(y, matcher.Y0))

            gammas = np.array(points)
            ax.plot(gammas.real, gammas.imag, color=color, linewidth=1.5, label=label)

            # Mark start and end
            ax.plot(gammas.real[0], gammas.imag[0], 'o', color=color, markersize=8)
            ax.plot(gammas.real[-1], gammas.imag[-1], 's', color=color, markersize=8)
        else:
            # Series topology: trace impedance path
            points = []

            gamma_load = impedance_to_gamma(matcher.Z_load, matcher.Z0)
            points.append(gamma_load)

            n_steps = 50
            for k in range(1, n_steps + 1):
                dist = matcher.l * k / n_steps
                z = matcher.transform_impedance(matcher.Z_load, dist)
                points.append(impedance_to_gamma(z, matcher.Z0))

            z_at_stub1 = matcher.transform_impedance(matcher.Z_load, matcher.l)
            for k in range(n_steps + 1):
                frac = k / n_steps
                z = z_at_stub1 + matcher.stub_impedance_series(l1) * frac
                points.append(impedance_to_gamma(z, matcher.Z0))

            z_after_stub1 = z_at_stub1 + matcher.stub_impedance_series(l1)
            for k in range(1, n_steps + 1):
                dist = matcher.d * k / n_steps
                z = matcher.transform_impedance(z_after_stub1, dist)
                points.append(impedance_to_gamma(z, matcher.Z0))

            z_at_stub2 = matcher.transform_impedance(z_after_stub1, matcher.d)
            for k in range(n_steps + 1):
                frac = k / n_steps
                z = z_at_stub2 + matcher.stub_impedance_series(l2) * frac
                points.append(impedance_to_gamma(z, matcher.Z0))

            gammas = np.array(points)
            ax.plot(gammas.real, gammas.imag, color=color, linewidth=1.5, label=label)
            ax.plot(gammas.real[0], gammas.imag[0], 'o', color=color, markersize=8)
            ax.plot(gammas.real[-1], gammas.imag[-1], 's', color=color, markersize=8)

    # Mark the center (matched point)
    ax.plot(0, 0, '+', color='black', markersize=12, markeredgewidth=2)

    ax.legend(loc='upper left')
    ax.set_xlabel('Real(\u0393)')
    ax.set_ylabel('Imag(\u0393)')

    plt.tight_layout()

    if output_file:
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        plt.close(fig)
    else:
        plt.show()


def plot_frequency_response(
    sweep_result: 'Union[FrequencySweepResult, List[FrequencySweepResult]]',
    output_file: Optional[str] = None,
) -> None:
    """
    Plot frequency response from one or more sweep results.

    Creates a 3-panel plot: |S11| vs frequency, VSWR vs frequency,
    and Return Loss vs frequency.  When multiple results are provided
    they are overlaid with different colours.

    Parameters
    ----------
    sweep_result : FrequencySweepResult or list of FrequencySweepResult
        Results from one or more frequency sweeps
    output_file : str, optional
        If provided, save the plot to this file instead of showing interactively

    Raises
    ------
    ImportError
        If matplotlib is not installed
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        raise ImportError(
            "matplotlib is required for frequency response plots. "
            "Install it with: pip install matplotlib  "
            "or: pip install double-stub[plot]"
        )

    # Normalise to list
    if not isinstance(sweep_result, list):
        results = [sweep_result]
    else:
        results = sweep_result

    colors = ['b', 'r', 'g', 'purple', 'orange', 'cyan']

    fig, axes = plt.subplots(3, 1, figsize=(10, 10), sharex=True)

    center_ghz = results[0].center_frequency / 1e9

    ax1 = axes[0]
    ax2 = axes[1]
    ax3 = axes[2]

    all_vswr: List[float] = []

    for i, sr in enumerate(results):
        freq_ghz = sr.frequencies / 1e9
        color = colors[i % len(colors)]
        label = f'Solution {i + 1}' if len(results) > 1 else None

        # Panel 1: |S11|
        ax1.plot(freq_ghz, sr.reflection_coefficient, color=color,
                 linewidth=1.5, label=label)

        # Panel 2: VSWR
        ax2.plot(freq_ghz, sr.vswr, color=color, linewidth=1.5, label=label)
        all_vswr.extend(sr.vswr.tolist())

        # Panel 3: Return Loss
        rl = sr.return_loss_db.copy()
        rl[np.isinf(rl)] = np.nan
        ax3.plot(freq_ghz, rl, color=color, linewidth=1.5, label=label)

    # Decorations
    ax1.axvline(center_ghz, color='gray', linestyle='--', alpha=0.7, label='Center freq')
    ax1.set_ylabel('|S11|')
    ax1.set_title('Frequency Response - Double-Stub Matching')
    ax1.grid(True, alpha=0.3)
    ax1.legend()

    ax2.axhline(2.0, color='orange', linestyle='--', alpha=0.7, label='VSWR = 2')
    ax2.axvline(center_ghz, color='gray', linestyle='--', alpha=0.7)
    ax2.set_ylabel('VSWR')
    max_vswr = max(all_vswr) if all_vswr else 3.0
    ax2.set_ylim(bottom=1.0, top=min(10.0, max(3.0, max_vswr * 1.1)))
    ax2.grid(True, alpha=0.3)
    ax2.legend()

    ax3.axhline(10.0, color='orange', linestyle='--', alpha=0.7, label='RL = 10 dB')
    ax3.axvline(center_ghz, color='gray', linestyle='--', alpha=0.7)
    ax3.set_ylabel('Return Loss (dB)')
    ax3.set_xlabel('Frequency (GHz)')
    ax3.grid(True, alpha=0.3)
    ax3.legend()

    plt.tight_layout()

    if output_file:
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        plt.close(fig)
    else:
        plt.show()
