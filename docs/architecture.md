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
| `solver` | Grid, Hamiltonian, eigenpairs, normalization, raw diagnostics | `models`, `potentials` |
| `validation` | Analytic errors, tolerances, and convergence evidence | `models`, `potentials` |
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
│   ├── test_models.py
│   ├── test_potentials.py
│   ├── test_solver.py
│   ├── test_validation.py
│   ├── test_figures.py
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

- The unit convention is dimensionless with `hbar = m = 1`, so the kinetic operator is
  `-0.5 d²/dx²`.
- `grid_points` counts both endpoints. Homogeneous Dirichlet boundaries set the wavefunction to
  zero at those endpoints; only the `grid_points - 2` interior values enter the Hamiltonian.
- Domains are finite and strictly increasing. A configuration has at least four total grid points,
  at least one requested eigenstate, and fewer eigenstates than interior points.
- Parameters have unique, trimmed names and finite real values. They are sorted into canonical
  immutable pairs, making `SimulationConfig` stable and safe to cache.
- `SimulationResult` owns read-only `float64` copies of every numerical array. Grid and potential
  arrays have shape `(grid_points,)`, energies have shape `(eigenstate_count,)`, and wavefunctions
  are state-major with shape `(eigenstate_count, grid_points)`.
- Results enforce a uniform increasing grid, configured endpoints, ascending energies, Dirichlet
  endpoint values, matching diagnostic shapes, and a finite non-negative solve time.
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

## Validation boundary

The infinite square well is the numerical oracle for the first milestone. In dimensionless units,
its exact energies are `E_n = pi^2 n^2 / (2 L^2)`, where `L` is the well width and `n` begins at
one. The harmonic oscillator uses `V(x) = 0.5 omega^2 x^2` and exact energies
`E_n = omega(n + 0.5)`, where `n` begins at zero. It approximates the unbounded problem on the
fixed domain `[-8, 8]` with 1,201 points so frequency remains the only user-facing oscillator
parameter.

A result is trustworthy only when all applicable checks pass:

| Check | MVP tolerance |
|---|---:|
| Maximum relative energy error, infinite well | `1e-4` |
| Maximum relative energy error, harmonic oscillator | `1.5e-4` |
| Maximum relative residual | `1e-8` |
| Maximum normalization error | `1e-12` |
| Maximum orthogonality error | `1e-12` |

Convergence evidence compares matching solutions in coarse-to-fine order. Relative energy errors
must decrease, and every adjacent-grid observed order must be within `0.1` of the second-order
target. The oscillator energy tolerance holds for all six states across the bounded frequency range
`0.5 <= omega <= 2.0`. These are transparent acceptance gates, not solver inputs; future
experiments can add their own analytic criteria without changing the shared numerical path.

### Symmetric double-well contract

The double well uses

`V(x) = V0 * ((2x / d)^2 - 1)^2`

on the fixed domain `[-6, 6]` with 1,201 grid points by default. This is the standard quartic
`lambda * (x^2 - a^2)^2` form reparameterized so the controls describe visible geometry directly:
`V0` is the central barrier height, while `d` is the full distance between the minima at
`x = +/-d/2`. The bounded controls are `2.5 <= V0 <= 8.0` and `2.0 <= d <= 4.0`.

The quartic double well has no elementary analytic spectrum, so its acceptance evidence differs
from the first two presets. Tests establish exact potential symmetry and geometry, even/odd parity
of the two lowest states, a positive low-state energy splitting, and decreasing splitting as either
barrier height or well separation increases. The lower barrier bound keeps both members of this
tunneling pair below the central barrier at every corner of the supported control space. Residual,
normalization, and orthogonality diagnostics still come from the same shared solver path.

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
For the double-well tunneling cycle, Streamlit owns one bounded `t/T` scrubber and the pure figure
builder computes a normalized snapshot from the lowest even/odd pair. The cached eigensolve is
reused as the user moves the control, so this adds no custom JavaScript or high-frame-rate solve loop.

The double-well view may pass a second immutable `SimulationResult` into the same figure builder as
comparison context. That result is always the cached default preset: its potential and two lowest
energy levels remain visually muted and fixed while the current solid traces respond to controls.
Turning comparison off removes both the reference traces and its metric delta; it never creates a
second solver or visualization path.

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
- [Plotly subplots](https://plotly.com/python/subplots/)
- [SciPy sparse eigensolver](https://docs.scipy.org/doc/scipy/reference/generated/scipy.sparse.linalg.eigsh.html)
- [MIT infinite-square-well derivation](https://ocw.mit.edu/courses/8-04-quantum-physics-i-spring-2016/resources/mit8_04s16_lecnotes11/)
- [MIT quantum-harmonic-oscillator derivation](https://ocw.mit.edu/courses/8-04-quantum-physics-i-spring-2013/resources/mit8_04s13_lec08/)
- [UCSB quartic double-well exercises](https://web.physics.ucsb.edu/~davidgrabovsky/files-teaching/Double%20Well%20Problems.pdf)
- [MIT double-well symmetry and tunneling lecture](https://ocw.mit.edu/courses/8-321-quantum-theory-i-fall-2017/resources/mit8_321f17_lec23/)
- [MIT centered second-difference derivation](https://math.mit.edu/icg/resources/teaching/18.085-spring2015/SecondOrder.pdf)
- [uv projects](https://docs.astral.sh/uv/concepts/projects/)
