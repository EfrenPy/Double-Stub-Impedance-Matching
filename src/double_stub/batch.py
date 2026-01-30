"""Batch processing for double-stub impedance matching calculations."""

import csv
import logging
from typing import Any, Dict, List, Optional

from .core import DoubleStubMatcher

logger = logging.getLogger(__name__)


def process_batch(input_file: str,
                  base_config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Process a batch of load impedances from a CSV file.

    The CSV file must have columns 'load_real' and 'load_imag'.

    Parameters
    ----------
    input_file : str
        Path to the CSV file
    base_config : dict
        Base configuration parameters (line_impedance, stub_impedance, etc.)

    Returns
    -------
    list of dict
        Results for each row, each containing:
        - load_impedance (complex): The load impedance processed
        - solutions (list): List of (l1, l2) pairs, or empty if failed
        - error (str or None): Error message if processing failed
    """
    results: List[Dict[str, Any]] = []

    with open(input_file, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row_num, row in enumerate(reader, 1):
            try:
                load_real = float(row['load_real'])
                load_imag = float(row['load_imag'])
                load_impedance = complex(load_real, load_imag)

                matcher = DoubleStubMatcher(
                    distance_to_first_stub=base_config['distance_to_first_stub'],
                    distance_between_stubs=base_config['distance_between_stubs'],
                    load_impedance=load_impedance,
                    line_impedance=base_config['line_impedance'],
                    stub_impedance=base_config['stub_impedance'],
                    stub_type=base_config.get('stub_type', 'short'),
                    precision=base_config.get('precision', 1e-8),
                    max_length=base_config.get('max_length', 0.5),
                    stub_topology=base_config.get('stub_topology', 'shunt'),
                )

                solutions = matcher.calculate()
                results.append({
                    'load_impedance': load_impedance,
                    'solutions': solutions,
                    'error': None,
                })
                logger.debug("Row %d: found %d solutions for Z_L=%s",
                             row_num, len(solutions), load_impedance)

            except Exception as e:
                logger.warning("Row %d failed: %s", row_num, e)
                try:
                    z: Optional[complex] = complex(
                        float(row.get('load_real', 0)),
                        float(row.get('load_imag', 0))
                    )
                except (ValueError, TypeError):
                    z = None
                results.append({
                    'load_impedance': z,
                    'solutions': [],
                    'error': str(e),
                })

    return results
