"""Tests for export functions."""

import csv
import io
import json

from double_stub.export import format_csv, format_json, format_text


def _sample_solutions():
    return [(0.065432, 0.123456), (0.234567, 0.345678)]


def _sample_config():
    return {
        'load_impedance': complex(38.9, -26.7),
        'line_impedance': 50.0,
        'stub_impedance': 50.0,
        'stub_type': 'short',
        'stub_topology': 'shunt',
        'distance_to_first_stub': 0.07,
        'distance_between_stubs': 0.375,
        'precision': 1e-8,
    }


def _sample_verification():
    return [
        {
            'valid': True,
            'reflection_coefficient': 1e-6,
            'error': 1e-6,
            'vswr': 1.000002,
            'return_loss_db': 120.0,
        },
        {
            'valid': True,
            'reflection_coefficient': 2e-6,
            'error': 2e-6,
            'vswr': 1.000004,
            'return_loss_db': 114.0,
        },
    ]


class TestFormatJson:
    def test_parseable(self):
        result = format_json(_sample_solutions(), _sample_config())
        data = json.loads(result)
        assert 'config' in data
        assert 'solutions' in data

    def test_solution_fields(self):
        result = format_json(_sample_solutions(), _sample_config())
        data = json.loads(result)
        sol = data['solutions'][0]
        assert 'l1_wavelengths' in sol
        assert 'l2_wavelengths' in sol
        assert 'l1_degrees' in sol
        assert 'l2_degrees' in sol

    def test_correct_count(self):
        result = format_json(_sample_solutions(), _sample_config())
        data = json.loads(result)
        assert len(data['solutions']) == 2


class TestFormatCsv:
    def test_valid_csv(self):
        result = format_csv(_sample_solutions(), _sample_config())
        reader = csv.reader(io.StringIO(result))
        rows = list(reader)
        assert len(rows) == 3  # header + 2 data rows

    def test_correct_columns(self):
        result = format_csv(_sample_solutions(), _sample_config())
        reader = csv.reader(io.StringIO(result))
        header = next(reader)
        assert header == ['solution', 'l1_wavelengths', 'l2_wavelengths',
                         'l1_degrees', 'l2_degrees']


class TestFormatText:
    def test_contains_header(self):
        result = format_text(_sample_solutions(), _sample_config())
        assert 'Double-Stub Impedance Matching Calculator' in result

    def test_contains_solutions(self):
        result = format_text(_sample_solutions(), _sample_config())
        assert 'Solution 1' in result
        assert 'Solution 2' in result

    def test_no_solutions(self):
        result = format_text([], _sample_config())
        assert 'No valid solutions found' in result

    def test_text_contains_vswr(self):
        result = format_text(_sample_solutions(), _sample_config(),
                             _sample_verification())
        assert 'VSWR' in result

    def test_text_contains_return_loss(self):
        result = format_text(_sample_solutions(), _sample_config(),
                             _sample_verification())
        assert 'Return Loss' in result


class TestFormatJsonVswr:
    def test_json_contains_vswr(self):
        result = format_json(_sample_solutions(), _sample_config(),
                             _sample_verification())
        data = json.loads(result)
        assert 'vswr' in data['solutions'][0]['verification']
        assert 'return_loss_db' in data['solutions'][0]['verification']


class TestFormatCsvVswr:
    def test_csv_contains_vswr_columns(self):
        result = format_csv(_sample_solutions(), _sample_config(),
                            _sample_verification())
        reader = csv.reader(io.StringIO(result))
        header = next(reader)
        assert 'vswr' in header
        assert 'return_loss_db' in header

    def test_csv_without_verification_no_extra_columns(self):
        result = format_csv(_sample_solutions(), _sample_config())
        reader = csv.reader(io.StringIO(result))
        header = next(reader)
        assert 'vswr' not in header


class TestFormatJsonInf:
    def test_json_with_inf_vswr(self):
        """JSON with inf VSWR should produce valid JSON with null."""
        solutions = [(0.1, 0.2)]
        config = _sample_config()
        verification = [{
            'valid': True,
            'reflection_coefficient': 1.0,
            'error': 0.0,
            'vswr': float('inf'),
            'return_loss_db': float('inf'),
        }]
        result = format_json(solutions, config, verification)
        data = json.loads(result)
        assert data['solutions'][0]['verification']['vswr'] is None
        assert data['solutions'][0]['verification']['return_loss_db'] is None


class TestFormatCsvInf:
    def test_csv_with_inf_values(self):
        """CSV with inf VSWR/RL should produce empty strings."""
        solutions = [(0.1, 0.2)]
        config = _sample_config()
        verification = [{
            'valid': True,
            'reflection_coefficient': 1.0,
            'error': 0.0,
            'vswr': float('inf'),
            'return_loss_db': float('inf'),
        }]
        result = format_csv(solutions, config, verification)
        reader = csv.reader(io.StringIO(result))
        header = next(reader)
        row = next(reader)
        # vswr and return_loss_db are the last two columns
        vswr_idx = header.index('vswr')
        rl_idx = header.index('return_loss_db')
        assert row[vswr_idx] == ""
        assert row[rl_idx] == ""


class TestFormatTouchstone:
    @staticmethod
    def _make_sweep():
        import numpy as np
        from double_stub.frequency_sweep import FrequencySweepResult
        freqs = np.linspace(0.5e9, 1.5e9, 5)
        gamma = np.array([0.3 + 0.1j, 0.1 + 0.05j, 0.001 + 0.0j,
                          0.1 - 0.05j, 0.3 - 0.1j])
        return FrequencySweepResult(
            frequencies=freqs,
            reflection_coefficient_complex=gamma,
            center_frequency=1e9,
            l1_wavelengths_center=0.1,
            l2_wavelengths_center=0.2,
        )

    def test_touchstone_header(self):
        from double_stub.export import format_touchstone
        result = format_touchstone(self._make_sweep())
        lines = result.strip().splitlines()
        # Find option line
        option_line = [l for l in lines if l.startswith('#')][0]
        assert '# GHz S MA R 50.0' == option_line

    def test_touchstone_data_lines(self):
        from double_stub.export import format_touchstone
        result = format_touchstone(self._make_sweep())
        data_lines = [l for l in result.strip().splitlines()
                      if not l.startswith('!') and not l.startswith('#')]
        assert len(data_lines) == 5

    def test_touchstone_db_format(self):
        from double_stub.export import format_touchstone
        result = format_touchstone(self._make_sweep(), format_type='DB')
        assert '# GHz S DB R 50.0' in result

    def test_touchstone_ri_format(self):
        from double_stub.export import format_touchstone
        result = format_touchstone(self._make_sweep(), format_type='RI')
        assert '# GHz S RI R 50.0' in result

    def test_touchstone_case_insensitive_input(self):
        from double_stub.export import format_touchstone
        for unit_input, expected in [('ghz', 'GHz'), ('GHZ', 'GHz'),
                                     ('mhz', 'MHz'), ('MHz', 'MHz'),
                                     ('khz', 'kHz'), ('hz', 'Hz')]:
            result = format_touchstone(self._make_sweep(), freq_unit=unit_input)
            option_line = [l for l in result.strip().splitlines()
                           if l.startswith('#')][0]
            assert f'# {expected} S MA R 50.0' == option_line
