"""Command-line interface for the double-stub impedance matching calculator."""

import argparse
import logging
import sys
from typing import Any, Dict, List, Optional, cast

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
from .core import DoubleStubMatcher
from .export import format_csv, format_json, format_text
from .utils import parse_complex_impedance


def main(argv: Optional[List[str]] = None) -> int:
    """Main program entry point.

    Parameters
    ----------
    argv : list of str, optional
        Command-line arguments. Defaults to sys.argv[1:].

    Returns
    -------
    int
        Exit code (0 for success, 1 for error).
    """
    parser = argparse.ArgumentParser(
        description='Calculate double-stub impedance matching solutions',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --load "38.9,-26.7" --distance-to-stub 0.07 --stub-spacing 0.375
  %(prog)s --load "60,40" --line-impedance 75 --stub-type open
  %(prog)s --output-format json --load "38.9,-26.7"
  %(prog)s --batch loads.csv --output-format csv
  %(prog)s --stub-topology series --load "100,50"
        """
    )

    parser.add_argument('-l', '--distance-to-stub', type=float,
                        default=DEFAULT_DISTANCE_TO_FIRST_STUB,
                        help=f'Distance from load to first stub (wavelengths, '
                             f'default: {DEFAULT_DISTANCE_TO_FIRST_STUB})')

    parser.add_argument('-d', '--stub-spacing', type=float,
                        default=DEFAULT_DISTANCE_BETWEEN_STUBS,
                        help=f'Distance between stubs (wavelengths, '
                             f'default: {DEFAULT_DISTANCE_BETWEEN_STUBS})')

    parser.add_argument('-z', '--load', type=str,
                        default=DEFAULT_LOAD_IMPEDANCE,
                        help=f'Load impedance as "real,imaginary" '
                             f'(default: {DEFAULT_LOAD_IMPEDANCE})')

    parser.add_argument('-Z0', '--line-impedance', type=float,
                        default=DEFAULT_LINE_IMPEDANCE,
                        help=f'Characteristic impedance of line (Ohms, '
                             f'default: {DEFAULT_LINE_IMPEDANCE})')

    parser.add_argument('-Zs', '--stub-impedance', type=float,
                        default=DEFAULT_STUB_IMPEDANCE,
                        help=f'Characteristic impedance of stubs (Ohms, '
                             f'default: {DEFAULT_STUB_IMPEDANCE})')

    parser.add_argument('-t', '--stub-type', type=str,
                        choices=['short', 'open'],
                        default=DEFAULT_STUB_TYPE,
                        help=f'Stub type: short or open (default: {DEFAULT_STUB_TYPE})')

    parser.add_argument('-p', '--precision', type=float,
                        default=DEFAULT_PRECISION,
                        help=f'Numerical precision (default: {DEFAULT_PRECISION})')

    parser.add_argument('--max-length', type=float,
                        default=DEFAULT_MAX_LENGTH,
                        help=f'Maximum stub length in wavelengths '
                             f'(default: {DEFAULT_MAX_LENGTH})')

    parser.add_argument('--stub-topology', type=str,
                        choices=['shunt', 'series'],
                        default=DEFAULT_STUB_TOPOLOGY,
                        help=f'Stub topology: shunt or series '
                             f'(default: {DEFAULT_STUB_TOPOLOGY})')

    parser.add_argument('--output-format', type=str,
                        choices=['text', 'json', 'csv'],
                        default='text',
                        help='Output format (default: text)')

    parser.add_argument('--batch', type=str, default=None,
                        metavar='FILE',
                        help='Batch mode: CSV file with load_real,load_imag columns')

    parser.add_argument('--plot', action='store_true',
                        help='Show Smith chart plot (requires matplotlib)')

    parser.add_argument('--save-plot', type=str, default=None,
                        metavar='FILE',
                        help='Save Smith chart plot to file (requires matplotlib)')

    parser.add_argument('--freq-sweep', type=str, default=None,
                        metavar='START,STOP,POINTS',
                        help='Frequency sweep as "start,stop,points" in Hz')

    parser.add_argument('--center-freq', type=float, default=None,
                        metavar='HZ',
                        help='Center (design) frequency in Hz for sweep')

    parser.add_argument('--save-freq-plot', type=str, default=None,
                        metavar='FILE',
                        help='Save frequency response plot to file')

    parser.add_argument('--export-s1p', type=str, default=None,
                        metavar='FILE',
                        help='Export Touchstone .s1p file (requires --freq-sweep)')

    parser.add_argument('--solution-index', type=int, default=None,
                        metavar='N',
                        help='Solution index (1-based) for frequency sweep. '
                             'If omitted, all solutions are swept.')

    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Enable verbose/debug output')

    args = parser.parse_args(argv)

    # Set up logging on the package namespace only (avoid polluting root logger)
    _logger = logging.getLogger('double_stub')
    if not _logger.handlers:
        _handler = logging.StreamHandler()
        _handler.setFormatter(logging.Formatter('%(name)s %(levelname)s: %(message)s'))
        _logger.addHandler(_handler)
    _logger.setLevel(logging.DEBUG if args.verbose else logging.WARNING)

    # Handle batch mode
    if args.batch:
        return _run_batch(args)

    return _run_single(args)


def _run_single(args: argparse.Namespace) -> int:
    """Run a single impedance matching calculation."""
    try:
        load_impedance = parse_complex_impedance(args.load)

        matcher = DoubleStubMatcher(
            distance_to_first_stub=args.distance_to_stub,
            distance_between_stubs=args.stub_spacing,
            load_impedance=load_impedance,
            line_impedance=args.line_impedance,
            stub_impedance=args.stub_impedance,
            stub_type=args.stub_type,
            precision=args.precision,
            max_length=args.max_length,
            stub_topology=args.stub_topology,
        )

        solutions = matcher.calculate()

        # Print forbidden region diagnostic if no solutions found
        if len(solutions) == 0:
            forbidden = matcher.check_forbidden_region()
            if forbidden['in_forbidden_region']:
                print(f"Diagnostic: {forbidden['message']}",
                      file=sys.stderr)

        # Verify solutions
        verification_results = []
        for l1, l2 in solutions:
            verification_results.append(matcher.verify_solution(l1, l2))

        config = {
            'load_impedance': load_impedance,
            'line_impedance': args.line_impedance,
            'stub_impedance': args.stub_impedance,
            'stub_type': args.stub_type,
            'stub_topology': args.stub_topology,
            'distance_to_first_stub': args.distance_to_stub,
            'distance_between_stubs': args.stub_spacing,
            'precision': args.precision,
            'max_length': args.max_length,
        }

        vr_dicts = cast(List[Dict[str, Any]], verification_results)
        if args.output_format == 'json':
            print(format_json(solutions, config, vr_dicts))
        elif args.output_format == 'csv':
            print(format_csv(solutions, config, vr_dicts), end='')
        else:
            print(format_text(solutions, config, vr_dicts))

        # Handle plotting
        if args.plot or args.save_plot:
            from .visualization import plot_smith_chart
            plot_smith_chart(matcher, solutions, output_file=args.save_plot)

        # Handle frequency sweep
        if args.freq_sweep and len(solutions) > 0:
            from .frequency_sweep import (
                frequency_sweep, format_sweep_table, rank_solutions,
            )

            try:
                parts = args.freq_sweep.split(',')
                if len(parts) != 3:
                    raise ValueError(
                        "freq-sweep must be 'start,stop,points'"
                    )
                freq_start = float(parts[0])
                freq_stop = float(parts[1])
                num_points = int(parts[2])
            except ValueError as e:
                print(f"Error parsing --freq-sweep: {e}", file=sys.stderr)
                return 1

            if freq_start >= freq_stop:
                print("Error: freq-sweep start must be less than stop",
                      file=sys.stderr)
                return 1
            if num_points < 2:
                print("Error: freq-sweep num_points must be at least 2",
                      file=sys.stderr)
                return 1

            if args.center_freq is None:
                print("Error: --center-freq is required with --freq-sweep",
                      file=sys.stderr)
                return 1

            if args.center_freq <= 0:
                print("Error: --center-freq must be positive",
                      file=sys.stderr)
                return 1

            # Determine which solutions to sweep
            sol_index = args.solution_index
            if sol_index is not None:
                if sol_index < 1 or sol_index > len(solutions):
                    print(f"Error: --solution-index {sol_index} out of "
                          f"range (1..{len(solutions)})",
                          file=sys.stderr)
                    return 1
                sweep_indices = [sol_index - 1]
            else:
                sweep_indices = list(range(len(solutions)))

            sweep_results = []
            for idx in sweep_indices:
                l1, l2 = solutions[idx]
                sr = frequency_sweep(
                    matcher, l1, l2,
                    center_freq=args.center_freq,
                    freq_start=freq_start,
                    freq_stop=freq_stop,
                    num_points=num_points,
                )
                sweep_results.append(sr)
                label = f"Solution {idx + 1}" if len(sweep_indices) > 1 else ''
                print("\n" + format_sweep_table(sr, label=label))

            # Print ranking summary when multiple solutions are swept
            if len(sweep_indices) > 1:
                rankings = rank_solutions(
                    matcher, solutions,
                    center_freq=args.center_freq,
                    freq_start=freq_start,
                    freq_stop=freq_stop,
                    num_points=num_points,
                )
                print("\nSolution Ranking (by 10 dB RL bandwidth):")
                print("=" * 70)
                print(f"{'Rank':>4s}  {'Sol#':>4s}  {'BW 3dB (MHz)':>12s}  "
                      f"{'BW 10dB (MHz)':>13s}  {'BW VSWR<2 (MHz)':>15s}  "
                      f"{'Frac BW%':>8s}  {'Q':>6s}")
                print("-" * 70)
                for rank, r in enumerate(rankings, 1):
                    q_str = f"{r['q_factor']:.1f}" if r['q_factor'] != float('inf') else "inf"
                    print(f"{rank:4d}  {r['solution_index']:4d}  "
                          f"{r['bandwidth_3db'] / 1e6:12.2f}  "
                          f"{r['bandwidth_10db_rl'] / 1e6:13.2f}  "
                          f"{r['bandwidth_vswr2'] / 1e6:15.2f}  "
                          f"{r['fractional_bandwidth']:8.1f}  "
                          f"{q_str:>6s}")

            if args.save_freq_plot:
                from .visualization import plot_frequency_response
                if len(sweep_results) == 1:
                    plot_frequency_response(
                        sweep_results[0],
                        output_file=args.save_freq_plot)
                else:
                    plot_frequency_response(
                        sweep_results,
                        output_file=args.save_freq_plot)

            if args.export_s1p:
                if sol_index is None and len(solutions) > 1:
                    print("Error: --solution-index is required with "
                          "--export-s1p when multiple solutions exist",
                          file=sys.stderr)
                    return 1
                from .export import format_touchstone
                touchstone_data = format_touchstone(sweep_results[0])
                with open(args.export_s1p, 'w') as f:
                    f.write(touchstone_data)
                print(f"Touchstone file saved to {args.export_s1p}")

        return 0 if len(solutions) > 0 else 1

    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


def _run_batch(args: argparse.Namespace) -> int:
    """Run batch processing mode."""
    from .batch import process_batch

    try:
        base_config = {
            'distance_to_first_stub': args.distance_to_stub,
            'distance_between_stubs': args.stub_spacing,
            'line_impedance': args.line_impedance,
            'stub_impedance': args.stub_impedance,
            'stub_type': args.stub_type,
            'precision': args.precision,
            'max_length': args.max_length,
            'stub_topology': args.stub_topology,
        }

        results = process_batch(args.batch, base_config)

        if args.output_format == 'json':
            import json
            output = []
            for r in results:
                entry = {
                    'load_impedance': {
                        'real': r['load_impedance'].real,
                        'imag': r['load_impedance'].imag,
                    } if r['load_impedance'] else None,
                    'solutions': [
                        {
                            'l1_wavelengths': l1,
                            'l2_wavelengths': l2,
                            'l1_degrees': l1 * 360,
                            'l2_degrees': l2 * 360,
                        }
                        for l1, l2 in r['solutions']
                    ],
                    'error': r['error'],
                }
                output.append(entry)
            print(json.dumps(output, indent=2))
        elif args.output_format == 'csv':
            print("load_real,load_imag,solution,l1_wavelengths,l2_wavelengths,"
                  "l1_degrees,l2_degrees,error")
            for r in results:
                z = r['load_impedance']
                if r['solutions']:
                    for i, (l1, l2) in enumerate(r['solutions'], 1):
                        print(f"{z.real:.4f},{z.imag:.4f},{i},"
                              f"{l1:.6f},{l2:.6f},{l1*360:.2f},{l2*360:.2f},")
                else:
                    err = r['error'] or 'no solutions'
                    print(f"{z.real if z else 0:.4f},{z.imag if z else 0:.4f},"
                          f"0,,,,,{err}")
        else:
            for r in results:
                z = r['load_impedance']
                print(f"\nLoad: {z}")
                if r['error']:
                    print(f"  Error: {r['error']}")
                elif r['solutions']:
                    for i, (l1, l2) in enumerate(r['solutions'], 1):
                        print(f"  Solution {i}: l1={l1:.6f}\u03bb, l2={l2:.6f}\u03bb")
                else:
                    print("  No solutions found")

        return 0

    except FileNotFoundError:
        print(f"Error: Batch file '{args.batch}' not found", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Batch processing error: {e}", file=sys.stderr)
        return 1
