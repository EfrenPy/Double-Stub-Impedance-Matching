"""Core calculation engine for double-stub impedance matching."""

import logging
from typing import Callable, Dict, List, Tuple

import numpy as np
import scipy.optimize as sco

from .utils import cot, remove_duplicate_solutions
from .validation import validate_parameters

logger = logging.getLogger(__name__)


try:
    from typing import TypedDict

    class VerificationResult(TypedDict):
        valid: bool
        input_admittance: complex
        target_admittance: complex
        reflection_coefficient: float
        error: float
        vswr: float
        return_loss_db: float
except ImportError:
    VerificationResult = Dict  # type: ignore[misc,assignment]


class DoubleStubMatcher:
    """
    Calculates double-stub impedance matching solutions.

    This class implements the double-stub matching technique for transforming
    a complex load impedance to match a transmission line's characteristic impedance.
    Supports both shunt (parallel) and series stub topologies.
    """

    def __init__(self, distance_to_first_stub: float,
                 distance_between_stubs: float,
                 load_impedance: complex,
                 line_impedance: float,
                 stub_impedance: float,
                 stub_type: str = 'short',
                 precision: float = 1e-8,
                 max_length: float = 0.5,
                 stub_topology: str = 'shunt') -> None:
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
        max_length : float, optional
            Maximum stub length in wavelengths
        stub_topology : str, optional
            Stub topology: 'shunt' (parallel) or 'series'
        """
        stub_type = stub_type.lower()
        stub_topology = stub_topology.lower()

        validate_parameters(
            line_impedance=line_impedance,
            stub_impedance=stub_impedance,
            load_impedance=load_impedance,
            distance_to_first_stub=distance_to_first_stub,
            distance_between_stubs=distance_between_stubs,
            precision=precision,
            max_length=max_length,
            stub_type=stub_type,
            stub_topology=stub_topology,
        )

        self.l: float = distance_to_first_stub
        self.d: float = distance_between_stubs
        self.Z_load: complex = load_impedance
        self.Z0: float = line_impedance
        self.Z0_stub: float = stub_impedance
        self.stub_type: str = stub_type
        self.precision: float = precision
        self.max_length: float = max_length
        self.stub_topology: str = stub_topology

        # Calculate admittances (easier for parallel stub calculations)
        self.Y0: float = 1.0 / self.Z0
        self.Y0_stub: float = 1.0 / self.Z0_stub
        self.Y_load: complex = 1.0 / self.Z_load

        # Lazy-cached transformed values at stub 1 location
        self._y_at_stub1_cache: complex = None  # type: ignore[assignment]
        self._z_at_stub1_cache: complex = None  # type: ignore[assignment]

    @property
    def _y_at_stub1(self) -> complex:
        """Cached admittance at stub 1 location (shunt topology)."""
        if self._y_at_stub1_cache is None:
            self._y_at_stub1_cache = self.transform_admittance(
                self.Y_load, self.l)
        return self._y_at_stub1_cache

    @property
    def _z_at_stub1(self) -> complex:
        """Cached impedance at stub 1 location (series topology)."""
        if self._z_at_stub1_cache is None:
            self._z_at_stub1_cache = self.transform_impedance(
                self.Z_load, self.l)
        return self._z_at_stub1_cache

    def transform_admittance(self, admittance: complex,
                             distance: float) -> complex:
        """
        Transform admittance along a transmission line.

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
        beta_l = 2 * np.pi * distance
        y_normalized = admittance / self.Y0

        numerator = y_normalized * np.cos(beta_l) + 1j * np.sin(beta_l)
        denominator = np.cos(beta_l) + 1j * np.sin(beta_l) * y_normalized

        return self.Y0 * numerator / denominator

    def transform_impedance(self, impedance: complex,
                            distance: float) -> complex:
        """
        Transform impedance along a transmission line.

        Parameters
        ----------
        impedance : complex
            Impedance at the starting point
        distance : float
            Distance to transform in wavelengths

        Returns
        -------
        complex
            Transformed impedance
        """
        beta_l = 2 * np.pi * distance
        z_normalized = impedance / self.Z0

        numerator = z_normalized * np.cos(beta_l) + 1j * np.sin(beta_l)
        denominator = np.cos(beta_l) + 1j * np.sin(beta_l) * z_normalized

        return self.Z0 * numerator / denominator

    def stub_admittance(self, length: float) -> complex:
        """
        Calculate the admittance contributed by a shunt stub.

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
            return -1j * self.Y0_stub * cot(beta_l)
        else:
            return 1j * self.Y0_stub * np.tan(beta_l)

    def stub_impedance_series(self, length: float) -> complex:
        """
        Calculate the impedance contributed by a series stub.

        Parameters
        ----------
        length : float
            Length of the stub in wavelengths

        Returns
        -------
        complex
            Impedance of the stub
        """
        beta_l = 2 * np.pi * length

        if self.stub_type == 'short':
            return 1j * self.Z0_stub * np.tan(beta_l)
        else:
            return -1j * self.Z0_stub * cot(beta_l)

    def objective_first_stub(self, length: float) -> float:
        """
        Objective function for finding the first stub length.

        Parameters
        ----------
        length : float
            Proposed length for the first stub

        Returns
        -------
        float
            Difference between actual and target real admittance/impedance
        """
        if self.stub_topology == 'shunt':
            y_after_stub1 = self._y_at_stub1 + self.stub_admittance(length)
            y_at_stub2 = self.transform_admittance(y_after_stub1, self.d)
            return y_at_stub2.real / self.Y0 - 1.0
        else:
            # Series topology: work in impedance domain
            z_after_stub1 = self._z_at_stub1 + self.stub_impedance_series(length)
            z_at_stub2 = self.transform_impedance(z_after_stub1, self.d)
            return z_at_stub2.real / self.Z0 - 1.0

    def objective_second_stub(self, length: float,
                              first_stub_length: float) -> float:
        """
        Objective function for finding the second stub length.

        Parameters
        ----------
        length : float
            Proposed length for the second stub
        first_stub_length : float
            Known length of the first stub

        Returns
        -------
        float
            Remaining imaginary admittance/impedance
        """
        if self.stub_topology == 'shunt':
            y_after_stub1 = self._y_at_stub1 + self.stub_admittance(first_stub_length)
            y_at_stub2 = self.transform_admittance(y_after_stub1, self.d)
            return y_at_stub2.imag + self.stub_admittance(length).imag
        else:
            z_after_stub1 = self._z_at_stub1 + self.stub_impedance_series(first_stub_length)
            z_at_stub2 = self.transform_impedance(z_after_stub1, self.d)
            return z_at_stub2.imag + self.stub_impedance_series(length).imag

    def _generate_smart_guesses(self, max_length: float,
                                num_per_period: int = 20) -> List[float]:
        """
        Generate initial guesses spread across each 0.5-wavelength period.

        Parameters
        ----------
        max_length : float
            Maximum stub length in wavelengths
        num_per_period : int
            Number of guesses per 0.5-wavelength period

        Returns
        -------
        list
            List of initial guess values
        """
        period = 0.5  # stub solutions repeat every 0.5 wavelengths
        num_periods = max(1, int(np.ceil(max_length / period)))
        guesses: List[float] = []
        for p in range(num_periods):
            start = p * period
            end = min((p + 1) * period, max_length)
            for k in range(1, num_per_period + 1):
                g = start + (end - start) * k / (num_per_period + 1)
                if 0 < g < max_length:
                    guesses.append(g)
        return guesses

    @staticmethod
    def _refine_with_sign_changes(objective_func: Callable[[float], float],
                                  guesses: List[float]) -> List[float]:
        """
        Detect zero crossings and add midpoint guesses.

        Parameters
        ----------
        objective_func : callable
            The objective function to evaluate
        guesses : list
            Existing guess values (must be sorted)

        Returns
        -------
        list
            Refined guesses including midpoints at sign changes
        """
        refined = list(guesses)
        values = []
        for g in guesses:
            try:
                values.append(float(objective_func(g)))
            except (RuntimeError, ValueError, FloatingPointError):
                values.append(float('nan'))

        for i in range(len(values) - 1):
            v1, v2 = values[i], values[i + 1]
            if np.isfinite(v1) and np.isfinite(v2) and v1 * v2 < 0:
                midpoint = (guesses[i] + guesses[i + 1]) / 2
                refined.append(midpoint)

        return sorted(refined)

    def _solve_stub2_analytically(self, l1: float) -> List[float]:
        """
        Solve for stub 2 length analytically using arctan.

        For shunt topology with short stubs:
            B_stub2 = -B_at_stub2
            -Y0_stub * cot(beta*l2) = -B_at_stub2
            cot(beta*l2) = B_at_stub2 / Y0_stub
            tan(beta*l2) = Y0_stub / B_at_stub2
            l2 = arctan(Y0_stub / B_at_stub2) / (2*pi)

        Parameters
        ----------
        l1 : float
            First stub length in wavelengths

        Returns
        -------
        list
            Candidate l2 values (may include solutions from multiple periods)
        """
        candidates: List[float] = []
        max_length = self.max_length

        if self.stub_topology == 'shunt':
            y_after_stub1 = self._y_at_stub1 + self.stub_admittance(l1)
            y_at_stub2 = self.transform_admittance(y_after_stub1, self.d)
            target_imag = -y_at_stub2.imag

            if self.stub_type == 'short':
                # -Y0_stub * cot(beta*l2) = target_imag
                # cot(beta*l2) = -target_imag / Y0_stub
                # tan(beta*l2) = -Y0_stub / target_imag
                if abs(target_imag) > 1e-15:
                    angle = np.arctan(-self.Y0_stub / target_imag)
                else:
                    angle = np.pi / 2  # cot -> 0 at pi/2
            else:
                # Y0_stub * tan(beta*l2) = target_imag
                # tan(beta*l2) = target_imag / Y0_stub
                angle = np.arctan(target_imag / self.Y0_stub)
        else:
            z_after_stub1 = self._z_at_stub1 + self.stub_impedance_series(l1)
            z_at_stub2 = self.transform_impedance(z_after_stub1, self.d)
            target_imag = -z_at_stub2.imag

            if self.stub_type == 'short':
                # Z0_stub * tan(beta*l2) = target_imag
                angle = np.arctan(target_imag / self.Z0_stub)
            else:
                # -Z0_stub * cot(beta*l2) = target_imag
                if abs(target_imag) > 1e-15:
                    angle = np.arctan(-self.Z0_stub / target_imag)
                else:
                    angle = np.pi / 2

        # Normalize angle to [0, pi) and generate candidates within max_length
        base_l = angle / (2 * np.pi)
        # Add half-wavelength multiples to cover all periods
        for n in range(-2, int(max_length / 0.5) + 3):
            l2_candidate = base_l + n * 0.5
            if 0 < l2_candidate < max_length:
                candidates.append(l2_candidate)

        # Refine each candidate with one fsolve step
        refined: List[float] = []
        for l2_guess in candidates:
            try:
                with np.errstate(divide='ignore', invalid='ignore'):
                    result = sco.fsolve(
                        lambda x: self.objective_second_stub(x, l1),
                        l2_guess,
                        xtol=self.precision,
                        full_output=True
                    )
                sol = result[0][0]
                info = result[1]
                if info['fvec'][0]**2 < self.precision and 0 < sol < max_length:
                    refined.append(sol)
            except (RuntimeError, ValueError, FloatingPointError):
                continue

        return refined

    def find_first_stub_solutions(self, num_trials: int = 50) -> List[float]:
        """
        Find all valid solutions for the first stub length.

        Uses smart initial guesses with sign-change detection. A small
        uniform sweep is added for robustness.

        Parameters
        ----------
        num_trials : int, optional
            Number of uniform sweep guesses to add (default 50).

        Returns
        -------
        list
            List of valid first stub lengths
        """
        solutions: List[float] = []
        max_length = self.max_length

        # Generate smart guesses and refine with sign changes
        guesses = self._generate_smart_guesses(max_length)
        guesses = self._refine_with_sign_changes(
            self.objective_first_stub, guesses)

        # Add uniform sweep guesses for robustness
        for i in range(1, num_trials):
            g = (max_length / num_trials) * i
            guesses.append(g)

        # Deduplicate guesses (sort and remove near-duplicates)
        guesses = sorted(set(round(g, 10) for g in guesses))

        for initial_guess in guesses:
            try:
                with np.errstate(divide='ignore', invalid='ignore'):
                    result = sco.fsolve(self.objective_first_stub, initial_guess,
                                        xtol=self.precision, full_output=True)
                solution = result[0][0]
                info = result[1]

                if info['fvec'][0]**2 < self.precision and 0 < solution < max_length:
                    solutions.append(solution)
                    logger.debug("First stub: found solution %.6f from guess %.6f",
                                 solution, initial_guess)
            except (RuntimeError, ValueError, FloatingPointError):
                continue

        unique = remove_duplicate_solutions(solutions, self.precision)
        logger.debug("First stub: %d unique solutions from %d candidates",
                     len(unique), len(solutions))
        return unique

    def find_second_stub_solutions(self, first_stub_lengths: List[float],
                                   num_trials: int = 50
                                   ) -> List[Tuple[float, float]]:
        """
        Find all valid solutions for the second stub length.

        Uses analytical arctan solution followed by numerical refinement,
        plus a small uniform sweep for robustness.

        Parameters
        ----------
        first_stub_lengths : list
            Valid first stub lengths
        num_trials : int, optional
            Number of uniform sweep guesses to add (default 50).

        Returns
        -------
        list of tuple
            List of (l1, l2) pairs
        """
        from .utils import remove_duplicate_pairs

        pairs: List[Tuple[float, float]] = []
        max_length = self.max_length

        for l1 in first_stub_lengths:
            l2_solutions: List[float] = []

            # Try analytical solution first
            analytical = self._solve_stub2_analytically(l1)
            l2_solutions.extend(analytical)

            # Also sweep numerically for robustness
            obj = lambda x: self.objective_second_stub(x, l1)  # noqa: E731
            guesses = self._generate_smart_guesses(max_length)
            guesses = self._refine_with_sign_changes(obj, guesses)

            for i in range(1, num_trials):
                guesses.append((max_length / num_trials) * i)

            guesses = sorted(set(round(g, 10) for g in guesses))

            for initial_guess in guesses:
                try:
                    with np.errstate(divide='ignore', invalid='ignore'):
                        result = sco.fsolve(
                            obj,
                            initial_guess,
                            xtol=self.precision,
                            full_output=True
                        )
                    solution = result[0][0]
                    info = result[1]

                    if info['fvec'][0]**2 < self.precision and 0 < solution < max_length:
                        l2_solutions.append(solution)
                except (RuntimeError, ValueError, FloatingPointError):
                    continue

            unique_l2 = remove_duplicate_solutions(l2_solutions, self.precision)
            for l2 in unique_l2:
                pairs.append((l1, l2))

        unique_pairs = remove_duplicate_pairs(pairs, self.precision)
        logger.debug("Second stub: %d unique pairs from %d candidates",
                     len(unique_pairs), len(pairs))
        return unique_pairs

    def check_forbidden_region(self) -> Dict[str, object]:
        """
        Check if the load falls in the double-stub forbidden region.

        For shunt topology, the forbidden region condition is:
            G'_L > Y0 / sin^2(beta*d)
        where G'_L is the real part of the load admittance transformed
        to the first stub location.

        For series topology, the analogous condition is:
            R'_L > Z0 / sin^2(beta*d)

        Returns
        -------
        dict
            Dictionary with keys:
            - in_forbidden_region (bool)
            - gl_prime (float): transformed conductance/resistance
            - threshold (float): maximum allowed value
            - message (str): diagnostic message
        """
        beta_d = 2 * np.pi * self.d

        sin_bd_sq = np.sin(beta_d) ** 2
        if sin_bd_sq < 1e-15:
            # sin(beta*d) ~ 0 means d ~ n*lambda/2, threshold is ~inf
            return {
                'in_forbidden_region': False,
                'gl_prime': 0.0,
                'threshold': float('inf'),
                'message': '',
            }

        if self.stub_topology == 'shunt':
            gl_prime = self._y_at_stub1.real
            threshold = self.Y0 / sin_bd_sq
            in_forbidden = gl_prime > threshold
            label = "conductance G'_L"
            unit_label = "Y0"
        else:
            gl_prime = self._z_at_stub1.real
            threshold = self.Z0 / sin_bd_sq
            in_forbidden = gl_prime > threshold
            label = "resistance R'_L"
            unit_label = "Z0"

        if in_forbidden:
            message = (
                f"Load is in the forbidden region: {label} = {gl_prime:.6f} "
                f"> {unit_label}/sin^2(beta*d) = {threshold:.6f}. "
                f"Suggestions: adjust stub spacing, use a different matching "
                f"technique (single-stub, quarter-wave transformer), or add "
                f"additional matching elements."
            )
        else:
            message = ''

        return {
            'in_forbidden_region': in_forbidden,
            'gl_prime': gl_prime,
            'threshold': threshold,
            'message': message,
        }

    def verify_solution(self, l1: float, l2: float,
                        tolerance: float = 1e-4) -> VerificationResult:
        """
        Verify that a pair of stub lengths achieves impedance matching.

        Plugs the stub lengths back through the full transformation chain
        and checks if the result matches the characteristic impedance.

        Parameters
        ----------
        l1 : float
            First stub length in wavelengths
        l2 : float
            Second stub length in wavelengths
        tolerance : float, optional
            Maximum acceptable reflection coefficient magnitude

        Returns
        -------
        dict
            Verification result with keys:
            - valid (bool): Whether the solution achieves matching
            - input_admittance (complex): Final admittance at the input
            - target_admittance (complex): Target admittance (Y0)
            - reflection_coefficient (float): Magnitude of reflection coefficient
            - error (float): Normalized admittance/impedance error
            - vswr (float): Voltage standing wave ratio
            - return_loss_db (float): Return loss in dB
        """
        if self.stub_topology == 'shunt':
            y_at_stub1 = self.transform_admittance(self.Y_load, self.l)
            y_after_stub1 = y_at_stub1 + self.stub_admittance(l1)
            y_at_stub2 = self.transform_admittance(y_after_stub1, self.d)
            y_final = y_at_stub2 + self.stub_admittance(l2)

            z_in = 1.0 / y_final
            gamma = (z_in - self.Z0) / (z_in + self.Z0)
            error = abs(y_final / self.Y0 - 1.0)

            gamma_mag = abs(gamma)
            vswr = (1 + gamma_mag) / (1 - gamma_mag) if gamma_mag < 1 else float('inf')
            return_loss_db = -20 * np.log10(gamma_mag) if gamma_mag > 0 else float('inf')

            return {
                'valid': gamma_mag < tolerance,
                'input_admittance': y_final,
                'target_admittance': self.Y0,
                'reflection_coefficient': gamma_mag,
                'error': error,
                'vswr': vswr,
                'return_loss_db': return_loss_db,
            }
        else:
            z_at_stub1 = self.transform_impedance(self.Z_load, self.l)
            z_after_stub1 = z_at_stub1 + self.stub_impedance_series(l1)
            z_at_stub2 = self.transform_impedance(z_after_stub1, self.d)
            z_final = z_at_stub2 + self.stub_impedance_series(l2)

            gamma = (z_final - self.Z0) / (z_final + self.Z0)
            y_final = 1.0 / z_final
            error = abs(z_final / self.Z0 - 1.0)

            gamma_mag = abs(gamma)
            vswr = (1 + gamma_mag) / (1 - gamma_mag) if gamma_mag < 1 else float('inf')
            return_loss_db = -20 * np.log10(gamma_mag) if gamma_mag > 0 else float('inf')

            return {
                'valid': gamma_mag < tolerance,
                'input_admittance': y_final,
                'target_admittance': self.Y0,
                'reflection_coefficient': gamma_mag,
                'error': error,
                'vswr': vswr,
                'return_loss_db': return_loss_db,
            }

    def _deduplicate_by_verification(
        self,
        pairs: List[Tuple[float, float]],
        tolerance: float = 1e-4,
    ) -> List[Tuple[float, float]]:
        """
        Deduplicate solution pairs by verifying and comparing results.

        Removes pairs that fail verification, then deduplicates by
        comparing both stub lengths (not input admittance, since all
        valid solutions converge to the same target). When two pairs
        have stub lengths within tolerance, the one with smaller total
        stub length is kept.

        Parameters
        ----------
        pairs : list of tuple
            Candidate (l1, l2) pairs
        tolerance : float
            Maximum acceptable |Gamma| for a valid solution

        Returns
        -------
        list of tuple
            Deduplicated, verified pairs
        """
        verified: List[Tuple[float, float]] = []
        for l1, l2 in pairs:
            vr = self.verify_solution(l1, l2, tolerance=tolerance)
            if vr['valid']:
                verified.append((l1, l2))

        # Deduplicate by comparing (l1, l2) values — pairs that
        # represent the same physical configuration.
        unique: List[Tuple[float, float]] = []
        dedup_tol = max(self.precision, 1e-6)
        for pair in verified:
            is_dup = False
            for idx, u_pair in enumerate(unique):
                if (abs(pair[0] - u_pair[0]) < dedup_tol
                        and abs(pair[1] - u_pair[1]) < dedup_tol):
                    # Keep the pair with shorter total stub length
                    if sum(pair) < sum(u_pair):
                        unique[idx] = pair
                    is_dup = True
                    break
            if not is_dup:
                unique.append(pair)

        return unique

    def calculate(self) -> List[Tuple[float, float]]:
        """
        Calculate all valid double-stub matching solutions.

        Returns
        -------
        list of tuples
            List of (first_stub_length, second_stub_length) pairs
        """
        # Check forbidden region first
        forbidden = self.check_forbidden_region()
        if forbidden['in_forbidden_region']:
            logger.warning("Forbidden region: %s", forbidden['message'])

        first_stub_solutions = self.find_first_stub_solutions()

        if len(first_stub_solutions) == 0:
            logger.warning("No valid solutions found for first stub")
            return []

        pairs = self.find_second_stub_solutions(first_stub_solutions)

        if len(pairs) == 0:
            logger.warning("No valid solutions found for second stub")
            return []

        pairs = self._deduplicate_by_verification(pairs)

        logger.debug("Found %d solution pair(s)", len(pairs))
        return pairs
