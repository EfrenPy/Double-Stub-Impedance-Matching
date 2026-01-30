"""Tests for visualization functions (headless with Agg backend)."""

import os

import matplotlib
matplotlib.use('Agg')

import numpy as np  # noqa: E402
import pytest  # noqa: E402

from double_stub.core import DoubleStubMatcher  # noqa: E402
from double_stub.frequency_sweep import FrequencySweepResult  # noqa: E402
from double_stub.visualization import plot_smith_chart, plot_frequency_response  # noqa: E402


@pytest.fixture
def shunt_matcher():
    return DoubleStubMatcher(
        distance_to_first_stub=0.07,
        distance_between_stubs=3.0 / 8.0,
        load_impedance=complex(38.9, -26.7),
        line_impedance=50.0,
        stub_impedance=50.0,
        stub_type='short',
        precision=1e-8,
    )


@pytest.fixture
def series_matcher():
    return DoubleStubMatcher(
        distance_to_first_stub=0.07,
        distance_between_stubs=3.0 / 8.0,
        load_impedance=complex(38.9, -26.7),
        line_impedance=50.0,
        stub_impedance=50.0,
        stub_type='short',
        stub_topology='series',
        precision=1e-8,
    )


class TestPlotSmithChart:
    def test_plot_runs_without_error(self, shunt_matcher):
        solutions = shunt_matcher.calculate()
        plot_smith_chart(shunt_matcher, solutions)

    def test_plot_saves_file(self, shunt_matcher, tmp_path):
        solutions = shunt_matcher.calculate()
        out_file = str(tmp_path / "smith.png")
        plot_smith_chart(shunt_matcher, solutions, output_file=out_file)
        assert os.path.exists(out_file)
        assert os.path.getsize(out_file) > 0

    def test_plot_series_topology(self, series_matcher, tmp_path):
        solutions = series_matcher.calculate()
        out_file = str(tmp_path / "smith_series.png")
        plot_smith_chart(series_matcher, solutions, output_file=out_file)
        assert os.path.exists(out_file)
        assert os.path.getsize(out_file) > 0

    def test_plot_empty_solutions(self, shunt_matcher, tmp_path):
        out_file = str(tmp_path / "smith_empty.png")
        plot_smith_chart(shunt_matcher, [], output_file=out_file)
        assert os.path.exists(out_file)


class TestPlotFrequencyResponse:
    @staticmethod
    def _make_sweep():
        freqs = np.linspace(0.5e9, 1.5e9, 11)
        gamma = np.linspace(0.3, 0.01, 11) * np.exp(1j * np.linspace(0, 1, 11))
        return FrequencySweepResult(
            frequencies=freqs,
            reflection_coefficient_complex=gamma,
            center_frequency=1e9,
            l1_wavelengths_center=0.1,
            l2_wavelengths_center=0.2,
        )

    def test_single_sweep_plot(self, tmp_path):
        out_file = str(tmp_path / "freq.png")
        plot_frequency_response(self._make_sweep(), output_file=out_file)
        assert os.path.exists(out_file)
        assert os.path.getsize(out_file) > 0

    def test_multi_sweep_plot(self, tmp_path):
        out_file = str(tmp_path / "freq_multi.png")
        plot_frequency_response(
            [self._make_sweep(), self._make_sweep()],
            output_file=out_file,
        )
        assert os.path.exists(out_file)
        assert os.path.getsize(out_file) > 0

    def test_shunt_topology_full(self, shunt_matcher, tmp_path):
        from double_stub.frequency_sweep import frequency_sweep
        solutions = shunt_matcher.calculate()
        l1, l2 = solutions[0]
        sr = frequency_sweep(
            shunt_matcher, l1, l2,
            center_freq=1e9, freq_start=0.5e9, freq_stop=1.5e9,
            num_points=11,
        )
        out_file = str(tmp_path / "freq_shunt.png")
        plot_frequency_response(sr, output_file=out_file)
        assert os.path.exists(out_file)

    def test_series_topology_full(self, series_matcher, tmp_path):
        from double_stub.frequency_sweep import frequency_sweep
        solutions = series_matcher.calculate()
        if len(solutions) > 0:
            l1, l2 = solutions[0]
            sr = frequency_sweep(
                series_matcher, l1, l2,
                center_freq=1e9, freq_start=0.5e9, freq_stop=1.5e9,
                num_points=11,
            )
            out_file = str(tmp_path / "freq_series.png")
            plot_frequency_response(sr, output_file=out_file)
            assert os.path.exists(out_file)
