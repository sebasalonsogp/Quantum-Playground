# Changelog

All notable user-facing changes to Quantum Playground are recorded here.

## Unreleased

### Added

- An interactive double-well tunneling cycle that moves a normalized two-state probability density
  between the wells and reports its live left-well probability and tunneling period.

## [0.1.0] - 2026-09-11

### Added

- Three interactive one-dimensional quantum experiments: infinite square well, harmonic
  oscillator, and symmetric double well.
- Coordinated potential, energy-level, wavefunction, and probability-density visualization.
- A flagship tunneling comparison that exposes the lowest even/odd energy split.
- Analytic validation, numerical diagnostics, and an on-demand convergence study.
- Bounded Streamlit controls, responsive presentation, keyboard navigation, and recovery guidance.
- A repeatable cold/warm runtime benchmark and GitHub Actions quality pipeline.

### Performance

- Shift-invert eigenvalue targeting keeps all representative and maximum-resolution solve paths
  below the 250 ms local budget on the recorded development machine.
