"""Tests for the command-line interface."""

import json
import os

import matplotlib
matplotlib.use('Agg')

from double_stub.cli import main  # noqa: E402


class TestCLI:
    def test_default_args(self):
        assert main([]) == 0

    def test_custom_load(self):
        assert main(['--load', '60,40']) == 0

    def test_invalid_load(self):
        assert main(['--load', 'invalid']) == 1

    def test_invalid_line_impedance(self):
        assert main(['--line-impedance', '0']) == 1

    def test_verbose_flag(self):
        assert main(['-v']) == 0

    def test_output_format_json(self, capsys):
        main(['--output-format', 'json'])
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert 'config' in data
        assert 'solutions' in data
        assert len(data['solutions']) > 0

    def test_output_format_csv(self, capsys):
        main(['--output-format', 'csv'])
        captured = capsys.readouterr()
        lines = captured.out.strip().splitlines()
        header = lines[0].strip()
        assert header.startswith('solution,l1_wavelengths,l2_wavelengths,l1_degrees,l2_degrees')
        assert len(lines) >= 2

    def test_stub_topology_series(self):
        assert main(['--stub-topology', 'series']) == 0

    def test_max_length_flag(self):
        assert main(['--max-length', '1.0']) == 0

    def test_open_stub_type(self):
        assert main(['--stub-type', 'open']) == 0

    def test_batch_mode_text_output(self, tmp_path, capsys):
        csv_file = tmp_path / "loads.csv"
        csv_file.write_text("load_real,load_imag\n38.9,-26.7\n60,40\n")
        result = main(['--batch', str(csv_file)])
        captured = capsys.readouterr()
        assert result == 0
        assert 'Load' in captured.out

    def test_batch_mode_json_output(self, tmp_path, capsys):
        csv_file = tmp_path / "loads.csv"
        csv_file.write_text("load_real,load_imag\n38.9,-26.7\n60,40\n")
        result = main(['--batch', str(csv_file), '--output-format', 'json'])
        captured = capsys.readouterr()
        assert result == 0
        data = json.loads(captured.out)
        assert len(data) == 2

    def test_freq_sweep_with_export_s1p(self, tmp_path, capsys):
        s1p_file = str(tmp_path / "out.s1p")
        result = main([
            '--freq-sweep', '0.5e9,1.5e9,5',
            '--center-freq', '1e9',
            '--export-s1p', s1p_file,
            '--solution-index', '1',
        ])
        assert result == 0
        assert os.path.exists(s1p_file)
        content = open(s1p_file).read()
        assert '# GHz S MA R 50.0' in content

    def test_freq_sweep_with_save_freq_plot(self, tmp_path):
        plot_file = str(tmp_path / "freq.png")
        result = main([
            '--freq-sweep', '0.5e9,1.5e9,5',
            '--center-freq', '1e9',
            '--save-freq-plot', plot_file,
            '--solution-index', '1',
        ])
        assert result == 0
        assert os.path.exists(plot_file)
        assert os.path.getsize(plot_file) > 0

    def test_forbidden_region_diagnostic(self, capsys):
        main([
            '--load', '10,0',
            '--distance-to-stub', '0.0',
            '--stub-spacing', '0.25',
        ])
        captured = capsys.readouterr()
        assert 'forbidden' in captured.err.lower()

    def test_export_s1p_without_solution_index(self, tmp_path, capsys):
        """--export-s1p without --solution-index should fail for multi-solution."""
        s1p_file = str(tmp_path / "out.s1p")
        result = main([
            '--freq-sweep', '0.5e9,1.5e9,5',
            '--center-freq', '1e9',
            '--export-s1p', s1p_file,
        ])
        captured = capsys.readouterr()
        assert result == 1
        assert 'solution-index' in captured.err.lower()

    def test_freq_sweep_start_ge_stop(self, capsys):
        result = main([
            '--freq-sweep', '1.5e9,0.5e9,5',
            '--center-freq', '1e9',
        ])
        captured = capsys.readouterr()
        assert result == 1
        assert 'start' in captured.err.lower()

    def test_freq_sweep_wrong_parts(self, capsys):
        result = main([
            '--freq-sweep', '0.5e9,1.5e9',
            '--center-freq', '1e9',
        ])
        assert result == 1

    def test_freq_sweep_num_points_lt_2(self, capsys):
        result = main([
            '--freq-sweep', '0.5e9,1.5e9,1',
            '--center-freq', '1e9',
        ])
        captured = capsys.readouterr()
        assert result == 1
        assert 'num_points' in captured.err.lower()

    def test_batch_file_not_found(self, capsys):
        result = main(['--batch', '/nonexistent/file.csv'])
        captured = capsys.readouterr()
        assert result == 1
        assert 'not found' in captured.err.lower()

    def test_center_freq_negative(self, capsys):
        result = main([
            '--freq-sweep', '0.5e9,1.5e9,11',
            '--center-freq', '-1',
        ])
        captured = capsys.readouterr()
        assert result == 1
        assert 'positive' in captured.err.lower()
