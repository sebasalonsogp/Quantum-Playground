# Quantum Playground

An interactive numerical playground for exploring how one-dimensional potential-energy
landscapes determine quantum energy levels, wavefunctions, and probability densities.

Quantum Playground is a focused portfolio project. It pairs a rigorously tested sparse
eigenvalue solver with a polished Streamlit and Plotly experience. Its scientific MVP provides
three curated experiments—an infinite square well, a harmonic oscillator, and a flagship double
well—while keeping numerical diagnostics available for deeper inspection.

## Status

All three interactive experiments are complete. Visitors can change bounded physical controls,
inspect six stationary states as wavefunctions or probability densities, and review numerical
evidence without leaving the shared solver workflow. The flagship symmetric double well adds a
fixed default comparison and makes tunneling-induced energy splitting the central observable.

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

The phased delivery strategy and task-level acceptance criteria are in the
[implementation plan](tasks/plan.md).

## Scope

The potential composer is intentionally deferred. The MVP prioritizes curated experiments,
one memorable double-well interaction, and visible numerical correctness.
