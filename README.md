# Double-Stub Impedance Matching Calculator

A Python tool for calculating double-stub impedance matching solutions in transmission line systems. This tool is designed for RF and microwave engineers working with impedance matching problems.

## Overview

Impedance matching is crucial in RF/microwave engineering to maximize power transfer and minimize reflections in transmission line systems. The double-stub matching technique uses two adjustable stubs (short-circuited or open-circuited transmission line sections) to transform a complex load impedance to match the characteristic impedance of the transmission line.

This calculator solves the nonlinear equations to determine the required stub lengths for impedance matching, typically yielding two valid solutions.

## Features

- **Comprehensive impedance matching**: Calculates stub lengths for both short-circuited and open-circuited stubs
- **Multiple solutions**: Automatically finds all valid matching configurations
- **Flexible configuration**: Command-line interface for easy parameter specification
- **Well-documented**: Detailed docstrings and comments throughout the code
- **Object-oriented design**: Clean, maintainable code structure using the `DoubleStubMatcher` class
- **Numerical precision control**: Adjustable tolerance for solution accuracy

## Installation

### Prerequisites

- Python 3.6 or higher
- NumPy
- SciPy

### Setup

1. Clone this repository:
```bash
git clone https://github.com/yourusername/Double-Stub-Impedance-Matching.git
cd Double-Stub-Impedance-Matching
```

2. Install required dependencies:
```bash
pip install numpy scipy
```

Or using a requirements file:
```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

Run with default parameters:
```bash
python double_stub.py
```

This uses the default configuration:
- Load impedance: 38.9 - j26.7 Ω
- Line impedance: 50 Ω
- Stub impedance: 50 Ω
- Distance to first stub: 0.07 λ
- Distance between stubs: 0.375 λ
- Stub type: short-circuited

### Custom Parameters

Specify your own parameters using command-line arguments:

```bash
python double_stub.py --load "60,40" --line-impedance 75 --stub-type open
```

### Command-Line Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--distance-to-stub` | `-l` | Distance from load to first stub (wavelengths) | 0.07 |
| `--stub-spacing` | `-d` | Distance between stubs (wavelengths) | 0.375 |
| `--load` | `-z` | Load impedance as "real,imaginary" | "38.9,-26.7" |
| `--line-impedance` | `-Z0` | Characteristic impedance of line (Ω) | 50.0 |
| `--stub-impedance` | `-Zs` | Characteristic impedance of stubs (Ω) | 50.0 |
| `--stub-type` | `-t` | Stub type: `short` or `open` | short |
| `--precision` | `-p` | Numerical precision | 1e-8 |

### Example Output

```
============================================================
Double-Stub Impedance Matching Calculator
============================================================
Load impedance:              38.90-26.70j Ω
Line impedance:              50.00 Ω
Stub impedance:              50.00 Ω
Stub type:                   short-circuited
Distance to first stub:      0.0700 λ
Distance between stubs:      0.3750 λ
Numerical precision:         1e-08
============================================================

Found 2 matching solution(s):

Solution 1:
  First stub length (l1):   0.065432 λ  (23.56°)
  Second stub length (l2):  0.123456 λ  (44.44°)

Solution 2:
  First stub length (l1):   0.234567 λ  (84.44°)
  Second stub length (l2):  0.345678 λ  (124.44°)
```

## Theory

### Double-Stub Matching Principle

The double-stub matching technique works by:

1. **First stub**: Adjusts the admittance to ensure the real part equals the characteristic admittance after transformation to the second stub location
2. **Second stub**: Cancels the remaining imaginary admittance to achieve a perfect match

The algorithm uses the transmission line equations in admittance form:

```
Y_in = Y0 * (Y_L/Y0 * cos(βl) + j*sin(βl)) / (cos(βl) + j*sin(βl) * Y_L/Y0)
```

Where:
- `Y_in` = input admittance
- `Y_L` = load admittance
- `Y0` = characteristic admittance
- `β` = phase constant (2π/λ)
- `l` = line length in wavelengths

### Stub Admittance

**Short-circuited stub:**
```
Y_stub = -j * Y0_stub * cot(βl)
```

**Open-circuited stub:**
```
Y_stub = j * Y0_stub * tan(βl)
```

### Limitations

Not all load impedances can be matched with double-stub matching. The technique has a "forbidden region" on the Smith chart where matching is impossible. If no solutions are found, your load may be in this region, and you may need to:
- Adjust the stub spacing
- Use a different matching technique (e.g., single-stub, quarter-wave transformer)
- Add additional matching elements

## Code Structure

```
double_stub.py
├── Utility Functions
│   ├── cot()                          # Cotangent function
│   ├── parse_complex_impedance()      # Parse impedance strings
│   └── remove_duplicate_solutions()   # Filter duplicate solutions
│
├── DoubleStubMatcher Class
│   ├── __init__()                     # Initialize matcher with parameters
│   ├── transform_admittance()         # Transform admittance along line
│   ├── stub_admittance()              # Calculate stub admittance
│   ├── objective_first_stub()         # Objective function for stub 1
│   ├── objective_second_stub()        # Objective function for stub 2
│   ├── find_first_stub_solutions()    # Solve for first stub length
│   ├── find_second_stub_solutions()   # Solve for second stub length
│   └── calculate()                    # Main calculation method
│
└── main()                             # CLI interface and program entry
```

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
1. Check the [Issues](https://github.com/yourusername/Double-Stub-Impedance-Matching/issues) page
2. Create a new issue with detailed information about your problem
3. Include the command you ran and the complete output

## Version History

- **v2.0** (2025) - Complete rewrite with English translation, OOP design, and CLI interface
- **v1.0** (2019) - Initial release with basic functionality
