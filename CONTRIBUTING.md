# Contributing to Double-Stub Impedance Matching Calculator

Thank you for your interest in contributing to this project! This document provides guidelines and instructions for contributing.

## Code of Conduct

By participating in this project, you agree to maintain a respectful and collaborative environment. Please be considerate and constructive in your communications.

## How Can I Contribute?

### Reporting Bugs

If you find a bug, please create an issue with the following information:

1. **Clear title**: Summarize the problem in the title
2. **Description**: Detailed description of the issue
3. **Steps to reproduce**:
   - Command or code that triggers the bug
   - Input parameters used
   - Expected behavior
   - Actual behavior
4. **Environment**:
   - Python version
   - NumPy version
   - SciPy version
   - Operating system
5. **Output**: Include the complete error message or unexpected output

**Example:**
```markdown
## Bug: Incorrect solution for open-circuited stubs

### Description
When using open-circuited stubs with certain load impedances, the calculator
returns solutions that don't actually match the load.

### Steps to Reproduce
```bash
python double_stub.py --load "100,50" --stub-type open
```

### Expected Behavior
Should return valid matching solutions or indicate no solution exists.

### Actual Behavior
Returns solutions that result in a mismatch when verified.

### Environment
- Python 3.9.7
- NumPy 1.21.2
- SciPy 1.7.1
- Ubuntu 20.04
```

### Suggesting Enhancements

We welcome suggestions for new features or improvements! Please create an issue with:

1. **Clear title**: Describe the enhancement
2. **Motivation**: Explain why this enhancement would be useful
3. **Proposed solution**: Describe how you envision it working
4. **Alternatives**: Any alternative approaches you've considered

**Examples of valuable enhancements:**
- Support for series stubs
- Visualization of solutions on a Smith chart
- Batch processing of multiple impedance values
- Export results to CSV or other formats
- GUI interface
- Verification mode to check if a solution is valid

### Pull Requests

We actively welcome your pull requests! Here's the process:

1. **Fork the repository** and create your branch from `master`
2. **Make your changes**:
   - Follow the code style guidelines below
   - Add tests if applicable
   - Update documentation as needed
3. **Test your changes** thoroughly
4. **Commit your changes** with clear, descriptive commit messages
5. **Push to your fork** and submit a pull request
6. **Describe your changes** in the pull request description

## Development Guidelines

### Code Style

This project follows standard Python conventions:

- **PEP 8**: Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide
- **Line length**: Maximum 100 characters (some flexibility for readability)
- **Indentation**: 4 spaces (no tabs)
- **Naming conventions**:
  - `snake_case` for functions and variables
  - `PascalCase` for classes
  - `UPPER_CASE` for constants
- **Docstrings**: Use NumPy-style docstrings for all public functions and classes

**Example:**
```python
def transform_admittance(self, admittance, distance):
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
    # Implementation here
    pass
```

### Code Organization

- **Modularity**: Keep functions focused on a single task
- **DRY principle**: Don't repeat yourself - extract common code into functions
- **Comments**: Use comments to explain *why*, not *what* (code should be self-documenting)
- **Type hints**: Consider adding type hints for better code clarity

### Testing

When adding new features:

1. **Manual testing**: Test with various input parameters
2. **Edge cases**: Consider boundary conditions (e.g., stub length = 0, very high/low impedances)
3. **Validation**: Verify solutions using transmission line theory or Smith chart
4. **Documentation**: Update README.md with new usage examples if applicable

### Commit Messages

Write clear, concise commit messages:

- **Format**: `<type>: <description>`
- **Types**:
  - `feat`: New feature
  - `fix`: Bug fix
  - `docs`: Documentation changes
  - `style`: Code style changes (formatting, no logic change)
  - `refactor`: Code refactoring
  - `test`: Adding or updating tests
  - `chore`: Maintenance tasks

**Examples:**
```
feat: Add support for series stub matching
fix: Correct cotangent calculation for small angles
docs: Update README with Smith chart visualization example
refactor: Extract duplicate solution removal into utility function
```

## Project Structure

Understanding the code structure will help you contribute effectively:

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
    frequency_sweep.py           # Frequency sweep analysis and bandwidth metrics

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

examples/
    basic_matching.py            # Basic matching example
    frequency_sweep_analysis.py  # Sweep, bandwidth, Q, group delay
    batch_processing.py          # Loop over loads programmatically

double_stub_cli.py               # Backwards compatibility wrapper
```

## Areas for Contribution

Here are some areas where contributions would be particularly valuable:

### High Priority
- [ ] RF analysis extensions (Smith chart overlays, noise figure integration)
- [ ] Support for lossy transmission lines (attenuation modelling)
- [ ] Interactive web calculator (e.g., Streamlit or Panel)

### Medium Priority
- [ ] Support for unequal stub impedances
- [ ] Single-stub matching as an alternative
- [ ] Triple-stub matching support
- [ ] GUI interface using tkinter or PyQt

### Low Priority
- [ ] Integration with commercial EDA tools (SPICE export)
- [ ] Automated design-space exploration
- [ ] Monte-Carlo tolerance analysis

## Questions?

If you have questions about contributing:

1. Check existing issues and pull requests
2. Create a new issue with the `question` label
3. Reach out to the maintainers

## Recognition

All contributors will be acknowledged in the project. Significant contributions may result in being added as a project maintainer.

## License

By contributing to this project, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to the Double-Stub Impedance Matching Calculator!
