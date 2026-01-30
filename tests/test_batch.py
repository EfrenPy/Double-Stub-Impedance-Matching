"""Tests for batch processing."""

import os
import tempfile

import pytest

from double_stub.batch import process_batch


def _base_config():
    return {
        'distance_to_first_stub': 0.07,
        'distance_between_stubs': 3.0 / 8.0,
        'line_impedance': 50.0,
        'stub_impedance': 50.0,
        'stub_type': 'short',
        'precision': 1e-8,
        'max_length': 0.5,
        'stub_topology': 'shunt',
    }


class TestBatchProcessing:
    def test_multiple_loads(self, tmp_path):
        csv_file = tmp_path / "loads.csv"
        csv_file.write_text("load_real,load_imag\n38.9,-26.7\n100,0\n60,40\n")

        results = process_batch(str(csv_file), _base_config())
        assert len(results) == 3
        for r in results:
            assert r['error'] is None
            assert len(r['solutions']) > 0

    def test_invalid_row_does_not_crash(self, tmp_path):
        csv_file = tmp_path / "loads.csv"
        csv_file.write_text("load_real,load_imag\n38.9,-26.7\nabc,def\n60,40\n")

        results = process_batch(str(csv_file), _base_config())
        assert len(results) == 3
        # First and third should succeed
        assert results[0]['error'] is None
        assert results[2]['error'] is None
        # Second should have an error
        assert results[1]['error'] is not None

    def test_empty_csv(self, tmp_path):
        csv_file = tmp_path / "empty.csv"
        csv_file.write_text("load_real,load_imag\n")

        results = process_batch(str(csv_file), _base_config())
        assert len(results) == 0
