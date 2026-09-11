# Quantum Playground Architecture

## Goal

Keep the application small while making the scientific implementation credible. The numerical
core is independently testable, the Streamlit layer remains thin, and the potential boundary leaves
room for a future composer without speculative infrastructure.

## Capability map

| Module | Responsibility | Depends on |
|---|---|---|
| `models` | Immutable simulation inputs, results, and diagnostics | — |
| `potentials` | Presets and parameter validation | `models` |
| `solver` | Grid, Hamiltonian, eigenpairs, ordering, normalization | `models`, `potentials` |
| `validation` | Analytic errors, residuals, orthogonality, convergence | `models`, `solver` |
| `figures` | Coordinated Plotly figures | `models` |
| `app` | Streamlit state, controls, explanations, and rendering | all provider modules |

Build order:

`models → potentials → solver → validation → figures → app`

Dependencies flow in one direction. Scientific modules never import Streamlit.

## Structure

```text
quantum-playground/
├── app.py
├── pyproject.toml
├── uv.lock
├── .python-version
├── .streamlit/
│   └── config.toml
├── .github/
│   └── workflows/
│       └── ci.yml
├── src/
│   └── quantum_playground/
│       ├── __init__.py
│       ├── models.py
│       ├── potentials.py
│       ├── solver.py
│       ├── validation.py
│       └── figures.py
├── tests/
│   ├── test_potentials.py
│   ├── test_solver.py
│   ├── test_validation.py
│   └── test_app.py
├── docs/
│   ├── product-brief.md
│   └── architecture.md
├── assets/
├── README.md
└── .gitignore
```

Modules are created only with their first real behavior. Avoid empty `utils`, `services`, nested
`core`, or component hierarchies.

## Core boundary

```python
@dataclass(frozen=True, slots=True)
class SimulationConfig:
    experiment: ExperimentId
    grid_points: int
    domain: tuple[float, float]
    eigenstate_count: int
    parameters: tuple[tuple[str, float], ...]


def solve(config: SimulationConfig) -> SimulationResult:
    """Return ordered, normalized low-energy states and diagnostics."""
```

- Configuration uses canonical parameter pairs and is safe to cache.
- Numerical arrays are returned in `SimulationResult`; plots are built separately.
- Potentials are pure callables mapping a grid and validated parameters to `V(x)`.
- Presets and a future composer must feed the same solver path.

## Runtime flow

```text
preset and controls
        ↓
SimulationConfig
        ↓
potential V(x)
        ↓
sparse Hamiltonian
        ↓
lowest eigenpairs
        ↓
normalization and diagnostics
        ↓
SimulationResult
      ↙      ↘
Plotly figure  numerical details
```

## Streamlit boundary

`app.py` owns page configuration, controls, session state, cached solver calls, explanations,
rendering, and user-facing error states. Start with ordinary reruns. Add bounded `st.cache_data`
after the result contract is stable, and use `st.fragment` only if profiling demonstrates a useful
responsiveness improvement.

The MVP will not contain custom JavaScript. If the potential composer enters scope, first evaluate
a focused Streamlit Components v2 drawing component with bidirectional state. A separate frontend
is justified only if that escape hatch proves insufficient.

## Visualization boundary

`figures.py` builds Plotly figures without calling Streamlit. Prefer one coordinated figure so the
potential, energy levels, wavefunctions, and probability densities share axes and visual language.
Client-side Plotly frames may animate precomputed states; repeated server-side solves should not be
used as a high-frame-rate animation loop.

## Testing

- Unit-test potentials, eigenpair ordering, normalization, orthogonality, residuals, analytic error,
  and convergence.
- Keep scientific tests deterministic and independent of Streamlit.
- Use Streamlit `AppTest` for initial load, experiment selection, reset, and recomputation.
- Test figure structure selectively; do not maintain pixel snapshots for every chart.
- Perform real-browser visual and performance review at UI milestones.

## Commands

```text
Install:       uv sync --all-groups
Run:           uv run streamlit run app.py
Test:          uv run pytest
Lint:          uv run ruff check .
Format check:  uv run ruff format --check .
Format:        uv run ruff format .
```

## Boundaries

Always:

- State units, boundaries, parameter ranges, and tolerances explicitly.
- Keep scientific computation independent from Streamlit.
- Add tests with numerical behavior changes.
- Measure before introducing optimization.

Ask first:

- Add runtime dependencies or experiments.
- Change numerical conventions.
- Add custom JavaScript, a component, or deployment infrastructure.
- Promote the potential composer into active scope.

Never:

- Evaluate arbitrary user-supplied Python or mathematical expressions.
- Hide convergence failures or silently return partial results.
- Create a separate numerical path for the potential composer.
- Commit secrets, environments, caches, or generated build output.

## Official references

- [Streamlit Plotly integration](https://docs.streamlit.io/develop/api-reference/charts/st.plotly_chart)
- [Streamlit fragments](https://docs.streamlit.io/develop/api-reference/execution-flow/st.fragment)
- [Streamlit Components v2](https://docs.streamlit.io/develop/concepts/custom-components/components-v2)
- [Plotly animations](https://plotly.com/python/animations/)
- [SciPy sparse eigensolver](https://docs.scipy.org/doc/scipy/reference/generated/scipy.sparse.linalg.eigsh.html)
- [uv projects](https://docs.astral.sh/uv/concepts/projects/)
