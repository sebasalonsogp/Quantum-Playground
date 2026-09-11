# Quantum Playground

An interactive numerical playground for exploring how one-dimensional potential-energy
landscapes determine quantum energy levels, wavefunctions, and probability densities.

Quantum Playground is a focused portfolio project. It pairs a rigorously tested sparse
eigenvalue solver with a polished Streamlit and Plotly experience. The MVP will provide three
curated experiments—an infinite square well, a harmonic oscillator, and a flagship double
well—while keeping numerical diagnostics available for deeper inspection.

## Status

Project scaffold. The first implementation milestone is an analytically validated infinite
square-well solver; no numerical behavior has been implemented yet.

## Planned stack

- Python 3.12
- NumPy and SciPy
- Streamlit and Plotly
- pytest and Streamlit AppTest
- Ruff
- uv

## Development

```powershell
uv sync --all-groups
uv run streamlit run app.py
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

## Architecture

The scientific package remains independent from Streamlit, with one-way dependencies from
the application shell into typed models, potential definitions, the solver, validation, and
visualization. See [docs/architecture.md](docs/architecture.md) for the approved boundaries.

The motivation, target audience, MVP, success criteria, and exclusions are recorded in the
[product brief](docs/product-brief.md).

## Scope

The potential composer is intentionally deferred. The MVP prioritizes curated experiments,
one memorable double-well interaction, and visible numerical correctness.
