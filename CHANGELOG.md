# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [2.5.1] - 2026-01-31

### Added
- Published to PyPI via trusted OIDC workflow (`pip install double-stub`).
- PyPI installation instructions in README.

### Changed
- Smith chart visualization: shunt topology now draws an admittance grid (constant-G, constant-B) so stub additions trace along constant-conductance circles; series topology keeps the impedance grid.
- Smith chart title indicates chart type: "Smith Chart (Admittance)" or "Smith Chart (Impedance)".
- Grid drawing extracted into `_draw_smith_grid()` helper with `chart_type` parameter.
- Shunt stub traces now use admittance-plane reflection coefficient `Γ_Y = (Y₀ − Y)/(Y₀ + Y)`.
- Minimum Python version raised from 3.8 to 3.10.
- CI matrix updated to test Python 3.10, 3.12, and 3.13.
- Updated pinned action SHAs in publish workflow.
- Updated example plots and documentation.

### Fixed
- Constant-reactance arcs were invisible: both arc angles evaluated to −90° producing zero-span arcs. Corrected by computing the actual second intersection point of each reactance circle with the unit circle.
- All Smith chart grid elements (resistance circles, reactance arcs) now clipped to the unit circle via `set_clip_path`.
- Resolved all 25 mypy strict type errors across 6 source files.
- Fixed 5 flake8 E127 indentation warnings in visualization.py.
- Publish workflow: `pypa/gh-action-pypi-publish` pinned SHA had no Docker image on GHCR; switched to `release/v1` tag.

## [2.5.0] - 2026-01-30

### Added
- Bandwidth metrics: 3 dB, 10 dB return-loss, and VSWR < 2 bandwidths as lazy properties on `FrequencySweepResult`.
- Fractional bandwidth and loaded Q factor properties.
- Unwrapped S11 phase (`phase_deg`) and group delay (`group_delay_ns`) lazy properties.
- `rank_solutions()` function to rank solution pairs by bandwidth.
- Ranking summary table printed in CLI when sweeping multiple solutions.
- Bandwidth summary appended to `format_sweep_table()` output.
- NaN/infinity rejection in load impedance validation.
- Scientific notation support in j-format impedance parser (`"1e2+j50"`).
- Frequency sweep parameter validation in CLI (start < stop, num_points >= 2, center_freq > 0).
- `examples/` directory with `basic_matching.py`, `frequency_sweep_analysis.py`, and `batch_processing.py`.
- Tests for NaN/inf validation, JSON/CSV inf handling, scientific notation parsing, bandwidth metrics, group delay, and solution ranking.

### Changed
- `VerificationResult` TypedDict now uses `total=True` (all fields always present).
- `_refine_with_sign_changes` type hint corrected from `object` to `Callable[[float], float]`.
- CONTRIBUTING.md updated to reflect modular `src/double_stub/` layout and current contribution areas.
- README.md roadmap updated to reflect completed and upcoming features.

### Fixed
- JSON export produced invalid JSON when VSWR or return loss was `inf` or `NaN`; now outputs `null`.
- CSV export formatted `inf` VSWR/return-loss as literal `inf`; now outputs empty string.
- Touchstone export could write NaN/inf gamma values; now falls back to total reflection.

## [2.4.0] - 2026-01-30

### Added
- Multi-solution frequency sweep: `--freq-sweep` now sweeps all solutions by default, with `--solution-index` to select a specific one.
- Flexible impedance input parsing: supports `"R+jX"` / `"R-jX"` format in addition to `"real,imaginary"`, with whitespace tolerance.
- Solution deduplication by verification: pairs producing identical input admittance are consolidated.
- NaN safety in vectorised frequency sweep.
- Test coverage for `visualization.py` (headless Agg backend).
- Tests for `__main__.py` module entry point.
- Tests for batch mode, Touchstone export, frequency plot saving, and forbidden region diagnostics in CLI.
- CHANGELOG.md (this file).

### Changed
- Reduced default solver `num_trials` from 500 to 50; smart guesses and analytical solutions cover the search space efficiently.
- Frequency sweep internals vectorised with NumPy (no Python for-loop over frequency points).
- `format_sweep_table()` accepts an optional `label` parameter for headings.
- `plot_frequency_response()` accepts a list of sweep results to overlay multiple solutions.
- Touchstone header uses canonical frequency unit casing (`GHz`, `MHz`, `kHz`, `Hz`) instead of all-uppercase.
- Logging in CLI uses a namespaced handler (`double_stub`) instead of `logging.basicConfig()`, avoiding pollution of the root logger.
- CI: enabled pip caching via `actions/setup-python` and enforced `--cov-fail-under=70` coverage threshold.
- `py.typed` marker declared in `pyproject.toml` package-data for correct sdist/wheel inclusion.

### Fixed
- Touchstone `.s1p` header wrote `GHZ` instead of standard `GHz`.
- `py.typed` marker was not included in built packages.
- `logging.basicConfig()` in CLI polluted the root logger for library consumers.

## [2.3.0] - 2025

### Added
- Forbidden region detection with diagnostic messages and suggestions.
- Smart initial guess generation spread across 0.5-wavelength periods.
- Analytical arctan solution for second stub length.
- Sign-change detection and midpoint refinement for initial guesses.
- RuntimeWarning suppression during numerical solving.

### Fixed
- Solution pairing: each returned (l1, l2) pair is now correctly associated and verified.

## [2.2.0] - 2025

### Added
- VSWR and return loss output for each solution.
- Frequency sweep analysis across a frequency band.
- Frequency response plots (3-panel: |S11|, VSWR, return loss).
- Touchstone `.s1p` file export.
- Full type hints throughout the codebase.

## [2.1.0] - 2025

### Added
- Package restructure as installable Python package.
- Series stub topology support.
- JSON and CSV output formats.
- Batch processing from CSV files.
- Smith chart visualization.
- Solution verification with reflection coefficient.
- Input parameter validation with clear error messages.
- Configurable maximum stub length.

## [2.0.0] - 2025

### Changed
- Complete rewrite with English translation, object-oriented design, and CLI interface.

## [1.0.0] - 2019

### Added
- Initial release with basic double-stub impedance matching functionality.
