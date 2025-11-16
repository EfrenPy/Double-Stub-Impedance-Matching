#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Double-Stub Impedance Matching Calculator

This script calculates the required stub lengths for double-stub impedance matching
in transmission line systems. It solves for stub lengths that transform a complex
load impedance to match the characteristic impedance of the transmission line.

Author: Efren Rodriguez Rodriguez
Created: Mon Oct 14 10:22:44 2019
"""

import numpy as np
import scipy.optimize as sco
import sys
import argparse


# ==================== Default Configuration ====================
# These values are used for testing/demonstration purposes
# Use command-line arguments or modify these values as needed

DEFAULT_DISTANCE_TO_FIRST_STUB = 0.07  # Distance from load to first stub (wavelengths)
DEFAULT_DISTANCE_BETWEEN_STUBS = 3.0 / 8.0  # Distance between stubs (wavelengths)
DEFAULT_LOAD_IMPEDANCE = '38.9,-26.7'  # Load impedance in format "real,imaginary"
DEFAULT_LINE_IMPEDANCE = 50.0  # Characteristic impedance of transmission line (Ohms)
DEFAULT_STUB_IMPEDANCE = 50.0  # Characteristic impedance of stubs (Ohms)
DEFAULT_STUB_TYPE = 'short'  # 'short' for short-circuited, 'open' for open-circuited
DEFAULT_PRECISION = 1e-8  # Numerical tolerance for solutions


# ==================== Utility Functions ====================

def cot(x):
    """
    Calculate cotangent (not defined in numpy).

    Parameters
    ----------
    x : float or ndarray
        Angle in radians

    Returns
    -------
    float or ndarray
        Cotangent of x
    """
    return np.cos(x) / np.sin(x)


def parse_complex_impedance(impedance_str):
    """
    Parse complex impedance from string format.

    Parameters
    ----------
    impedance_str : str
        Impedance in format "real,imaginary" (e.g., "38.9,-26.7")

    Returns
    -------
    complex
        Complex impedance value
    """
    parts = impedance_str.split(',')
    if len(parts) != 2:
        raise ValueError("Impedance must be in format 'real,imaginary'")
    return complex(float(parts[0]), float(parts[1]))


def remove_duplicate_solutions(solutions, tolerance):
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

    unique_solutions = []
    for sol in solutions:
        is_duplicate = False
        for unique_sol in unique_solutions:
            if np.abs(sol - unique_sol) < tolerance:
                is_duplicate = True
                break
        if not is_duplicate:
            unique_solutions.append(sol)

    return unique_solutions


# ==================== Main Calculation Class ====================

class DoubleStubMatcher:
    """
    Calculates double-stub impedance matching solutions.

    This class implements the double-stub matching technique for transforming
    a complex load impedance to match a transmission line's characteristic impedance.
    """

    def __init__(self, distance_to_first_stub, distance_between_stubs,
                 load_impedance, line_impedance, stub_impedance,
                 stub_type='short', precision=1e-8):
        """
        Initialize the double-stub matcher.

        Parameters
        ----------
        distance_to_first_stub : float
            Distance from load to first stub in wavelengths
        distance_between_stubs : float
            Distance between the two stubs in wavelengths
        load_impedance : complex
            Complex load impedance (Ohms)
        line_impedance : float
            Characteristic impedance of the transmission line (Ohms)
        stub_impedance : float
            Characteristic impedance of the stubs (Ohms)
        stub_type : str, optional
            Type of stub: 'short' for short-circuited, 'open' for open-circuited
        precision : float, optional
            Numerical tolerance for solutions
        """
        self.l = distance_to_first_stub
        self.d = distance_between_stubs
        self.Z_load = load_impedance
        self.Z0 = line_impedance
        self.Z0_stub = stub_impedance
        self.stub_type = stub_type.lower()
        self.precision = precision

        # Calculate admittances (easier for parallel stub calculations)
        self.Y0 = 1.0 / self.Z0
        self.Y0_stub = 1.0 / self.Z0_stub
        self.Y_load = 1.0 / self.Z_load

        # Validate stub type
        if self.stub_type not in ['short', 'open']:
            raise ValueError("Stub type must be 'short' or 'open'")

    def transform_admittance(self, admittance, distance):
        """
        Transform admittance along a transmission line.

        Uses the transmission line equation to calculate the input admittance
        at a distance from a known admittance.

        Parameters
        ----------
        admittance : complex
            Admittance at the starting point
        distance : float
            Distance to transform in wavelengths

        Returns
        -------
        complex
            Transformed admittance
        """
        beta_l = 2 * np.pi * distance  # Electrical length
        y_normalized = admittance / self.Y0

        numerator = y_normalized * np.cos(beta_l) + 1j * np.sin(beta_l)
        denominator = np.cos(beta_l) + 1j * np.sin(beta_l) * y_normalized

        return self.Y0 * numerator / denominator

    def stub_admittance(self, length):
        """
        Calculate the admittance contributed by a stub.

        Parameters
        ----------
        length : float
            Length of the stub in wavelengths

        Returns
        -------
        complex
            Admittance of the stub
        """
        beta_l = 2 * np.pi * length

        if self.stub_type == 'short':
            # Short-circuited stub
            return -1j * self.Y0_stub * cot(beta_l)
        else:
            # Open-circuited stub
            return 1j * self.Y0_stub * np.tan(beta_l)

    def objective_first_stub(self, length):
        """
        Objective function for finding the first stub length.

        The goal is to make the real part of the admittance equal to Y0
        after adding the first stub and transforming to the second stub location.

        Parameters
        ----------
        length : float
            Proposed length for the first stub

        Returns
        -------
        float
            Difference between actual and target real admittance
        """
        # Transform load admittance to first stub location
        y_at_stub1 = self.transform_admittance(self.Y_load, self.l)

        # Add first stub admittance
        y_after_stub1 = y_at_stub1 + self.stub_admittance(length)

        # Transform to second stub location
        y_at_stub2 = self.transform_admittance(y_after_stub1, self.d)

        # We want Re(y_at_stub2) = Y0
        return y_at_stub2.real / self.Y0 - 1.0

    def objective_second_stub(self, length, first_stub_length):
        """
        Objective function for finding the second stub length.

        Given the first stub length, find the second stub length that
        cancels the imaginary part of the admittance.

        Parameters
        ----------
        length : float
            Proposed length for the second stub
        first_stub_length : float
            Known length of the first stub

        Returns
        -------
        float
            Remaining imaginary admittance
        """
        # Transform load admittance to first stub location
        y_at_stub1 = self.transform_admittance(self.Y_load, self.l)

        # Add first stub admittance
        y_after_stub1 = y_at_stub1 + self.stub_admittance(first_stub_length)

        # Transform to second stub location
        y_at_stub2 = self.transform_admittance(y_after_stub1, self.d)

        # Add second stub and check if imaginary part is cancelled
        return y_at_stub2.imag + self.stub_admittance(length).imag

    def find_first_stub_solutions(self, num_trials=500, max_length=0.5):
        """
        Find all valid solutions for the first stub length.

        Parameters
        ----------
        num_trials : int, optional
            Number of different initial values to try
        max_length : float, optional
            Maximum stub length to consider (wavelengths)

        Returns
        -------
        list
            List of valid first stub lengths
        """
        solutions = []

        for i in range(1, num_trials):
            initial_guess = (max_length / num_trials) * i

            try:
                result = sco.fsolve(self.objective_first_stub, initial_guess,
                                   xtol=self.precision, full_output=True)
                solution = result[0][0]
                info = result[1]

                # Check if solution converged and is within valid range
                if info['fvec'][0]**2 < self.precision and 0 < solution < max_length:
                    solutions.append(solution)
            except:
                # Skip if solver fails
                continue

        # Remove duplicates
        return remove_duplicate_solutions(solutions, self.precision)

    def find_second_stub_solutions(self, first_stub_lengths, num_trials=500, max_length=0.5):
        """
        Find all valid solutions for the second stub length.

        Parameters
        ----------
        first_stub_lengths : list
            Valid first stub lengths
        num_trials : int, optional
            Number of different initial values to try
        max_length : float, optional
            Maximum stub length to consider (wavelengths)

        Returns
        -------
        list
            List of valid second stub lengths
        """
        solutions = []

        for l1 in first_stub_lengths:
            for i in range(1, num_trials):
                initial_guess = (max_length / num_trials) * i

                try:
                    result = sco.fsolve(
                        lambda x: self.objective_second_stub(x, l1),
                        initial_guess,
                        xtol=self.precision,
                        full_output=True
                    )
                    solution = result[0][0]
                    info = result[1]

                    # Check if solution converged and is within valid range
                    if info['fvec'][0]**2 < self.precision and 0 < solution < max_length:
                        solutions.append(solution)
                except:
                    # Skip if solver fails
                    continue

        # Remove duplicates
        return remove_duplicate_solutions(solutions, self.precision)

    def calculate(self):
        """
        Calculate all valid double-stub matching solutions.

        Returns
        -------
        list of tuples
            List of (first_stub_length, second_stub_length) pairs
        """
        # Find first stub solutions
        first_stub_solutions = self.find_first_stub_solutions()

        if len(first_stub_solutions) == 0:
            print("Warning: No valid solutions found for first stub")
            return []

        # Find second stub solutions
        second_stub_solutions = self.find_second_stub_solutions(first_stub_solutions)

        if len(second_stub_solutions) == 0:
            print("Warning: No valid solutions found for second stub")
            return []

        # Pair up solutions (typically get 2 valid pairs)
        solutions = []
        min_pairs = min(len(first_stub_solutions), len(second_stub_solutions))

        for i in range(min_pairs):
            solutions.append((first_stub_solutions[i], second_stub_solutions[i]))

        return solutions


# ==================== Main Program ====================

def main():
    """Main program entry point."""
    parser = argparse.ArgumentParser(
        description='Calculate double-stub impedance matching solutions',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --load "38.9,-26.7" --distance-to-stub 0.07 --stub-spacing 0.375
  %(prog)s --load "60,40" --line-impedance 75 --stub-type open
        """
    )

    parser.add_argument('-l', '--distance-to-stub', type=float,
                       default=DEFAULT_DISTANCE_TO_FIRST_STUB,
                       help=f'Distance from load to first stub (wavelengths, default: {DEFAULT_DISTANCE_TO_FIRST_STUB})')

    parser.add_argument('-d', '--stub-spacing', type=float,
                       default=DEFAULT_DISTANCE_BETWEEN_STUBS,
                       help=f'Distance between stubs (wavelengths, default: {DEFAULT_DISTANCE_BETWEEN_STUBS})')

    parser.add_argument('-z', '--load', type=str,
                       default=DEFAULT_LOAD_IMPEDANCE,
                       help=f'Load impedance as "real,imaginary" (default: {DEFAULT_LOAD_IMPEDANCE})')

    parser.add_argument('-Z0', '--line-impedance', type=float,
                       default=DEFAULT_LINE_IMPEDANCE,
                       help=f'Characteristic impedance of line (Ohms, default: {DEFAULT_LINE_IMPEDANCE})')

    parser.add_argument('-Zs', '--stub-impedance', type=float,
                       default=DEFAULT_STUB_IMPEDANCE,
                       help=f'Characteristic impedance of stubs (Ohms, default: {DEFAULT_STUB_IMPEDANCE})')

    parser.add_argument('-t', '--stub-type', type=str,
                       choices=['short', 'open'],
                       default=DEFAULT_STUB_TYPE,
                       help=f'Stub type: short or open (default: {DEFAULT_STUB_TYPE})')

    parser.add_argument('-p', '--precision', type=float,
                       default=DEFAULT_PRECISION,
                       help=f'Numerical precision (default: {DEFAULT_PRECISION})')

    args = parser.parse_args()

    try:
        # Parse load impedance
        load_impedance = parse_complex_impedance(args.load)

        # Create matcher object
        matcher = DoubleStubMatcher(
            distance_to_first_stub=args.distance_to_stub,
            distance_between_stubs=args.stub_spacing,
            load_impedance=load_impedance,
            line_impedance=args.line_impedance,
            stub_impedance=args.stub_impedance,
            stub_type=args.stub_type,
            precision=args.precision
        )

        # Display configuration
        print("=" * 60)
        print("Double-Stub Impedance Matching Calculator")
        print("=" * 60)
        print(f"Load impedance:              {load_impedance:.2f} Ω")
        print(f"Line impedance:              {args.line_impedance:.2f} Ω")
        print(f"Stub impedance:              {args.stub_impedance:.2f} Ω")
        print(f"Stub type:                   {args.stub_type}-circuited")
        print(f"Distance to first stub:      {args.distance_to_stub:.4f} λ")
        print(f"Distance between stubs:      {args.stub_spacing:.4f} λ")
        print(f"Numerical precision:         {args.precision}")
        print("=" * 60)

        # Calculate solutions
        solutions = matcher.calculate()

        # Display results
        if len(solutions) == 0:
            print("\nNo valid solutions found!")
            print("This may occur if the load is outside the matchable region.")
            return 1

        print(f"\nFound {len(solutions)} matching solution(s):\n")

        for i, (l1, l2) in enumerate(solutions, 1):
            print(f"Solution {i}:")
            print(f"  First stub length (l1):   {l1:.6f} λ  ({l1*360:.2f}°)")
            print(f"  Second stub length (l2):  {l2:.6f} λ  ({l2*360:.2f}°)")
            print()

        return 0

    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
