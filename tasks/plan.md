# Implementation Plan: Quantum Playground MVP

## Outcome

Deliver a public, recruiter-friendly Streamlit application that lets a visitor understand the
project within 30 seconds, create a meaningful quantum result within 90 seconds, and inspect enough
numerical evidence to trust the result. The MVP ends with three curated one-dimensional systems,
one memorable double-well interaction, automated scientific validation, and a deployed demo.

## Delivery strategy

- Build the infinite square well first because it gives us an analytic oracle and exposes numerical
  mistakes before they spread into the interface.
- Turn that verified kernel into a complete user-facing slice before adding experiment breadth.
- Add the harmonic oscillator and double well through the same configuration, solver, result, and
  figure contracts; no experiment-specific solver paths.
- Keep `app.py` responsible for interaction and presentation while `src/quantum_playground/`
  remains independent of Streamlit.
- Use tests first for scientific behavior and focused Streamlit `AppTest` coverage for critical
  interactions. Add caching or fragments only after measurement.
- Land each numbered task as a small, reviewable commit. Run a checkpoint after every two to four
  tasks so the application remains demonstrable throughout development.

## Dependency map

```text
models and conventions
        |
infinite-well potential
        |
sparse eigensolver
        |
diagnostics and analytic validation
       / \
Plotly figure   numerical evidence
       \ /
infinite-well user journey
        |
harmonic-oscillator slice
        |
double-well scientific slice
        |
double-well flagship experience
        |
polish, hardening, deployment
```

The future potential composer may replace a preset as a producer of sampled `V(x)`, but it may not
bypass or duplicate the shared numerical path.

## Phases

### Phase 1: Trustworthy scientific foundation

Tasks 1-4 establish immutable contracts, the infinite-well preset, the finite-difference solver,
and quantitative validation. This is the highest-risk phase and should fail early if the numerical
approach or performance budget is unsuitable.

**Exit gate:** Low-energy states match the analytic infinite-well solution; normalization,
orthogonality, and residual checks pass; refinement reduces error; the default solve is timed.

### Phase 2: First complete recruiter-facing slice

Tasks 5-6 convert the validated result into a coordinated Plotly figure and a guided Streamlit
journey. At this point, the project is small but genuinely demonstrable end to end.

**Exit gate:** A new visitor can load the infinite well, change grid resolution, inspect the
result, and understand the validation evidence without reading source code.

### Phase 3: Breadth and flagship depth

Tasks 7-9 add the harmonic oscillator and the double well through the existing boundaries, then
make tunneling-induced energy splitting the memorable centerpiece.

**Exit gate:** All three experiments use the same solver path, experiment switching is reliable,
and the double-well controls produce an obvious, interpretable change with baseline comparison.

### Phase 4: Product polish and engineering hardening

Tasks 10-12 improve numerical transparency, visual hierarchy, accessibility, resilience, and
measured responsiveness without expanding the scientific scope.

**Exit gate:** The two-minute portfolio journey is clear, keyboard-usable, robust to bounded input,
and normally updates within the documented performance budget.

### Phase 5: Portfolio delivery

Task 13 completes documentation, demo assets, CI evidence, deployment, and the final recruiter
acceptance pass.

**Exit gate:** The public repository and live application tell the same story, CI is green, setup is
reproducible from a clean clone, and the primary demo can be completed in under two minutes.

## Definition of done for every task

- Acceptance criteria and focused tests pass.
- `uv run ruff format --check .`, `uv run ruff check .`, and `uv run pytest` pass.
- No scientific logic is introduced into `app.py` or visualization code.
- User-visible numerical claims identify units, assumptions, or validation evidence where relevant.
- Documentation is updated when behavior or a public contract changes.
- The task leaves `main` runnable and does not introduce deferred abstractions or empty modules.

## Efficiency rules

- Prefer one vertical outcome per task and keep changes to roughly five files or fewer.
- Reuse presets for manual review and automated tests so the demo path is deterministic.
- Run the smallest focused test during development, then the full quality suite at checkpoints.
- Profile before optimizing. The default target is about 250 ms per local solve and under one second
  for a typical hosted interaction.
- Use client-side Plotly behavior only for already computed data; do not drive animation with rapid
  server-side eigensolves.
- Stop scope growth at the MVP boundary: no accounts, database, API service, custom JavaScript,
  arbitrary expressions, time dependence, or extra dimensions.

## Risks and mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Boundary-condition or normalization error produces convincing but wrong plots | High | Analytic infinite-well tests, residual checks, convergence evidence, and explicit grid conventions before UI work |
| Streamlit reruns feel sluggish | Medium | Bound grid/state counts, cache stable results after contracts settle, profile before fragments or components |
| Three experiments dilute the flagship | Medium | Keep controls sparse; treat the gallery as orientation and the double well as the deepest experience |
| Visual complexity overwhelms non-specialists | Medium | Progressive disclosure, coordinated axes, preset defaults, and a 30-second comprehension review |
| Numerical details clutter the primary journey | Low | Show a concise trust signal first and move diagnostics into an expandable panel |
| A future composer creates a second solver path | Medium | Preserve the sampled `V(x)` contract and require the composer to enter through it |

## Decisions intentionally deferred

- Repository license selection.
- Final visual brand details beyond the existing theme.
- Streamlit Community Cloud URL and deployment account configuration.
- Whether the post-MVP potential composer is valuable enough to schedule.

None of these decisions blocks Phases 1-4.

## Task tracking

Detailed acceptance criteria, dependencies, likely files, and verification commands are maintained
in [`tasks/todo.md`](todo.md). Implementation should begin only after this plan is reviewed.

## Backburner: potential composer

After the MVP is deployed and evaluated, run a separate feasibility phase. Its entry criteria are a
stable sampled-potential contract, acceptable Streamlit performance, and evidence that free-form
creation improves the portfolio experience. Start with a bounded drawing prototype using Streamlit
Components v2; do not accept executable Python or arbitrary mathematical expressions.
