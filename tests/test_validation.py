"""Tests for input validation."""

import pytest

from double_stub.validation import validate_parameters


class TestValidateParameters:
    def _valid_params(self, **overrides):
        params = dict(
            line_impedance=50.0,
            stub_impedance=50.0,
            load_impedance=complex(38.9, -26.7),
            distance_to_first_stub=0.07,
            distance_between_stubs=0.375,
            precision=1e-8,
            max_length=0.5,
            stub_type='short',
            stub_topology='shunt',
        )
        params.update(overrides)
        return params

    def test_valid_parameters(self):
        validate_parameters(**self._valid_params())

    def test_zero_line_impedance(self):
        with pytest.raises(ValueError, match="Line impedance must be positive"):
            validate_parameters(**self._valid_params(line_impedance=0))

    def test_negative_line_impedance(self):
        with pytest.raises(ValueError, match="Line impedance must be positive"):
            validate_parameters(**self._valid_params(line_impedance=-10))

    def test_zero_stub_impedance(self):
        with pytest.raises(ValueError, match="Stub impedance must be positive"):
            validate_parameters(**self._valid_params(stub_impedance=0))

    def test_negative_load_real(self):
        with pytest.raises(ValueError, match="non-negative"):
            validate_parameters(**self._valid_params(load_impedance=complex(-10, 5)))

    def test_zero_load_impedance(self):
        with pytest.raises(ValueError, match="cannot be zero"):
            validate_parameters(**self._valid_params(load_impedance=complex(0, 0)))

    def test_negative_distance_to_first_stub(self):
        with pytest.raises(ValueError, match="non-negative"):
            validate_parameters(**self._valid_params(distance_to_first_stub=-0.1))

    def test_zero_distance_between_stubs(self):
        with pytest.raises(ValueError, match="positive"):
            validate_parameters(**self._valid_params(distance_between_stubs=0))

    def test_negative_precision(self):
        with pytest.raises(ValueError, match="Precision must be positive"):
            validate_parameters(**self._valid_params(precision=-1e-8))

    def test_negative_max_length(self):
        with pytest.raises(ValueError, match="Max stub length must be positive"):
            validate_parameters(**self._valid_params(max_length=-0.5))

    def test_invalid_stub_type(self):
        with pytest.raises(ValueError, match="Stub type must be"):
            validate_parameters(**self._valid_params(stub_type='invalid'))

    def test_invalid_stub_topology(self):
        with pytest.raises(ValueError, match="Stub topology must be"):
            validate_parameters(**self._valid_params(stub_topology='invalid'))

    def test_zero_distance_to_first_stub_allowed(self):
        validate_parameters(**self._valid_params(distance_to_first_stub=0))

    def test_open_stub_type(self):
        validate_parameters(**self._valid_params(stub_type='open'))

    def test_series_topology(self):
        validate_parameters(**self._valid_params(stub_topology='series'))

    def test_nan_load_impedance(self):
        with pytest.raises(ValueError, match="NaN"):
            validate_parameters(**self._valid_params(
                load_impedance=complex(float('nan'), 0)))

    def test_nan_load_impedance_imag(self):
        with pytest.raises(ValueError, match="NaN"):
            validate_parameters(**self._valid_params(
                load_impedance=complex(50, float('nan'))))

    def test_inf_load_impedance(self):
        with pytest.raises(ValueError, match="infinity"):
            validate_parameters(**self._valid_params(
                load_impedance=complex(float('inf'), 0)))

    def test_inf_load_impedance_imag(self):
        with pytest.raises(ValueError, match="infinity"):
            validate_parameters(**self._valid_params(
                load_impedance=complex(50, float('inf'))))
