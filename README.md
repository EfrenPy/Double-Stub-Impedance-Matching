# Double-Stub Impedance Matching Calculator

A Python tool for calculating double-stub impedance matching solutions in transmission line systems. This tool is designed for RF and microwave engineers working with impedance matching problems.

## Overview

Impedance matching is crucial in RF/microwave engineering to maximize power transfer and minimize reflections in transmission line systems. The double-stub matching technique uses two adjustable stubs (short-circuited or open-circuited transmission line sections) to transform a complex load impedance to match the characteristic impedance of the transmission line.

This calculator solves the nonlinear equations to determine the required stub lengths for impedance matching, typically yielding two valid solutions.

## Features

- **Comprehensive impedance matching**: Calculates stub lengths for both short-circuited and open-circuited stubs
- **Shunt and series topologies**: Supports both parallel (shunt) and series stub configurations
- **Multiple solutions**: Automatically finds all valid matching configurations
- **Solution verification**: Verifies each solution by tracing the full transformation chain and computing the reflection coefficient
- **VSWR and return loss**: Reports VSWR and return loss (dB) for each solution
- **Frequency sweep**: Evaluates matching performance across a frequency band
- **Frequency response plots**: 3-panel plots of |S11|, VSWR, and return loss vs frequency
- **Touchstone export**: Export frequency sweep data to standard `.s1p` Touchstone format
- **Forbidden region detection**: Diagnoses when a load falls in the double-stub forbidden region
- **Multiple output formats**: Text, JSON, and CSV export
- **Batch processing**: Process multiple load impedances from a CSV file
- **Smith chart visualization**: Plot solutions on the Smith chart (requires matplotlib)
- **Input validation**: Comprehensive parameter validation with clear error messages
- **Configurable max stub length**: Limit stub lengths to a specified maximum
- **Flexible configuration**: Command-line interface for easy parameter specification
- **Numerical precision control**: Adjustable tolerance for solution accuracy

## Installation

### Prerequisites

- Python 3.10 or higher
- NumPy
- SciPy

### Setup

1. Clone this repository:
```bash
git clone https://github.com/EfrenPy/Double-Stub-Impedance-Matching.git
cd Double-Stub-Impedance-Matching
```

2. Install the package:
```bash
pip install -e .
```

For plotting support (Smith chart, frequency response):
```bash
pip install -e ".[plot]"
```

For development (tests, linting, type checking):
```bash
pip install -e ".[dev]"
```

Or install dependencies manually:
```bash
pip install numpy scipy
```

## Usage

### Basic Usage

Run with default parameters:
```bash
double-stub
```

Or using the backwards-compatible wrapper:
```bash
python double_stub_cli.py
```

This uses the default configuration:
- Load impedance: 38.9 - j26.7 Ohm
- Line impedance: 50 Ohm
- Stub impedance: 50 Ohm
- Distance to first stub: 0.07 lambda
- Distance between stubs: 0.375 lambda
- Stub type: short-circuited

### Custom Parameters

Specify your own parameters using command-line arguments:

```bash
double-stub --load "60,40" --line-impedance 75 --stub-type open
```

### Series Stubs

Use series stub topology instead of the default shunt (parallel):

```bash
double-stub --stub-topology series --load "100,50"
```

### JSON Export

```bash
double-stub --output-format json
```

### CSV Export

```bash
double-stub --output-format csv
```

### Batch Mode

Process multiple loads from a CSV file:

```bash
double-stub --batch loads.csv --output-format csv
```

The CSV file must have columns `load_real` and `load_imag`.

### Smith Chart

Display or save a Smith chart plot:

```bash
double-stub --plot
double-stub --save-plot smith.png
```

### Frequency Sweep

Evaluate matching performance across a frequency band:

```bash
double-stub --freq-sweep 0.5e9,1.5e9,101 --center-freq 1e9
```

Save frequency response plot or Touchstone file:

```bash
double-stub --freq-sweep 0.5e9,1.5e9,101 --center-freq 1e9 --save-freq-plot response.png
double-stub --freq-sweep 0.5e9,1.5e9,101 --center-freq 1e9 --export-s1p output.s1p
```

### Max Stub Length

Limit stub lengths to a specific maximum (in wavelengths):

```bash
double-stub --max-length 1.0
```

### Verbose Mode

Enable debug output:

```bash
double-stub -v
```

### Command-Line Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--distance-to-stub` | `-l` | Distance from load to first stub (wavelengths) | 0.07 |
| `--stub-spacing` | `-d` | Distance between stubs (wavelengths) | 0.375 |
| `--load` | `-z` | Load impedance as "real,imaginary" | "38.9,-26.7" |
| `--line-impedance` | `-Z0` | Characteristic impedance of line (Ohm) | 50.0 |
| `--stub-impedance` | `-Zs` | Characteristic impedance of stubs (Ohm) | 50.0 |
| `--stub-type` | `-t` | Stub type: `short` or `open` | short |
| `--stub-topology` | | Stub topology: `shunt` or `series` | shunt |
| `--max-length` | | Maximum stub length in wavelengths | 0.5 |
| `--precision` | `-p` | Numerical precision | 1e-8 |
| `--output-format` | | Output format: `text`, `json`, or `csv` | text |
| `--batch` | | CSV file for batch processing | |
| `--plot` | | Show Smith chart plot | |
| `--save-plot` | | Save Smith chart plot to file | |
| `--freq-sweep` | | Frequency sweep as "start,stop,points" | |
| `--center-freq` | | Center frequency in Hz for sweep | |
| `--save-freq-plot` | | Save frequency response plot to file | |
| `--export-s1p` | | Export Touchstone .s1p file | |
| `-v` / `--verbose` | | Enable verbose/debug output | |

### Example Output

```
============================================================
Double-Stub Impedance Matching Calculator
============================================================
Load impedance:              38.90-26.70j Ohm
Line impedance:              50.00 Ohm
Stub impedance:              50.00 Ohm
Stub type:                   short-circuited
Stub topology:               shunt
Distance to first stub:      0.0700 lambda
Distance between stubs:      0.3750 lambda
Numerical precision:         1e-08
============================================================

Found 2 matching solution(s):

Solution 1:
  First stub length (l1):   0.065432 lambda  (23.56 deg)
  Second stub length (l2):  0.123456 lambda  (44.44 deg)
  Verification:             PASS (|Gamma| = 0.000001)
  VSWR:                     1.000
  Return Loss:              119.59 dB

Solution 2:
  First stub length (l1):   0.234567 lambda  (84.44 deg)
  Second stub length (l2):  0.345678 lambda  (124.44 deg)
  Verification:             PASS (|Gamma| = 0.000002)
  VSWR:                     1.000
  Return Loss:              113.98 dB
```

## Example Plots

### Smith Chart

The Smith chart shows the transformation path for each matching solution, from the load point (circle) to the matched point (square) at the center. For shunt stub topologies, an admittance chart is used so that stub additions trace along constant-conductance circles; for series topologies, an impedance chart is used:

![Smith Chart](examples/smith_chart.png)

### Frequency Response

The frequency response plot shows |S11|, VSWR, and return loss across a 0.5--1.5 GHz band for each solution:

![Frequency Response](examples/frequency_response.png)

## Theory

### Double-Stub Matching Principle

The double-stub matching technique works by:

1. **First stub**: Adjusts the admittance to ensure the real part equals the characteristic admittance after transformation to the second stub location
2. **Second stub**: Cancels the remaining imaginary admittance to achieve a perfect match

The algorithm uses the transmission line equations in admittance form:

```
Y_in = Y0 * (Y_L/Y0 * cos(beta*l) + j*sin(beta*l)) / (cos(beta*l) + j*sin(beta*l) * Y_L/Y0)
```

Where:
- `Y_in` = input admittance
- `Y_L` = load admittance
- `Y0` = characteristic admittance
- `beta` = phase constant (2*pi/lambda)
- `l` = line length in wavelengths

### Stub Admittance

**Short-circuited stub:**
```
Y_stub = -j * Y0_stub * cot(beta*l)
```

**Open-circuited stub:**
```
Y_stub = j * Y0_stub * tan(beta*l)
```

### Forbidden Region

Not all load impedances can be matched with double-stub matching. The technique has a forbidden region where matching is impossible. For shunt topology, the condition is:

```
G'_L > Y0 / sin^2(beta*d)
```

where `G'_L` is the real part of the load admittance transformed to the first stub location, and `d` is the stub spacing. If no solutions are found, the calculator will diagnose whether the load falls in this forbidden region and suggest alternatives:
- Adjust the stub spacing
- Use a different matching technique (e.g., single-stub, quarter-wave transformer)
- Add additional matching elements

## Code Structure

```
src/double_stub/
    __init__.py                  # Package exports and version
    __main__.py                  # Module entry point (python -m double_stub)
    constants.py                 # Default configuration values
    core.py                      # Core calculation engine (DoubleStubMatcher)
    cli.py                       # Command-line interface
    utils.py                     # Utility functions (cot, parsing, deduplication)
    validation.py                # Input parameter validation
    export.py                    # Output formatting (text, JSON, CSV, Touchstone)
    batch.py                     # Batch processing from CSV files
    visualization.py             # Smith chart and frequency response plots
    frequency_sweep.py           # Frequency sweep analysis

tests/
    conftest.py                  # Shared test fixtures
    test_core.py                 # Core engine tests
    test_utils.py                # Utility function tests
    test_validation.py           # Validation tests
    test_cli.py                  # CLI tests
    test_export.py               # Export format tests
    test_batch.py                # Batch processing tests
    test_verification.py         # Solution verification tests
    test_frequency_sweep.py      # Frequency sweep tests

double_stub_cli.py               # Backwards compatibility wrapper
```

## Roadmap

Planned features and improvements:

- Lossy transmission line support (attenuation modelling)
- Interactive web calculator
- Support for unequal stub impedances

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Author

Efren Rodriguez Rodriguez

## Acknowledgments

- Based on classical transmission line theory and Smith chart techniques
- Uses SciPy's `fsolve` for solving nonlinear equations
- Inspired by standard RF/microwave engineering textbooks

## References

For more information on double-stub matching:
- Pozar, D. M. (2011). *Microwave Engineering* (4th ed.). Wiley.
- Collin, R. E. (1992). *Foundations for Microwave Engineering* (2nd ed.). IEEE Press.
- Smith Chart and impedance matching techniques in RF design

## Support

If you encounter any issues or have questions:
1. Check the [Issues](https://github.com/EfrenPy/Double-Stub-Impedance-Matching/issues) page
2. Create a new issue with detailed information about your problem
3. Include the command you ran and the complete output

## Version History

See [CHANGELOG.md](CHANGELOG.md) for a detailed list of changes in each release.
