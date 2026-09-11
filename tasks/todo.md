# Quantum Playground MVP Tasks

Complete tasks in order unless a dependency explicitly permits parallel work. Checkpoints are
release gates, not optional cleanup passes.

## Phase 1: Trustworthy scientific foundation

### Task 1: Define simulation contracts and conventions

**Description:** Add immutable, typed inputs and outputs that make units, domain boundaries, sampled
arrays, eigenstate ordering, and diagnostics explicit before numerical code depends on them.

**Acceptance criteria:**

- [x] `SimulationConfig`, experiment identifiers, result data, and diagnostics have stable typed contracts.
- [x] Invalid domains, grid sizes, state counts, and non-finite parameters are rejected clearly.
- [x] Dimensionless units (`hbar = m = 1`) and Dirichlet-boundary conventions are documented and tested.

**Verification:**

- [x] Focused tests: `uv run pytest tests/test_models.py`
- [x] Full quality suite passes.

**Dependencies:** None

**Files likely touched:** `src/quantum_playground/models.py`, `tests/test_models.py`,
`docs/architecture.md`

**Estimated scope:** Medium

### Task 2: Add the infinite-square-well preset

**Description:** Implement a validated preset that samples the infinite well on the shared grid and
provides deterministic defaults for scientific tests and the first demo.

**Acceptance criteria:**

- [ ] The well uses the documented domain and boundary convention.
- [ ] Preset metadata includes bounded defaults and concise user-facing explanatory text.
- [ ] Potential output has the expected shape, type, and finite interior values.

**Verification:**

- [ ] Focused tests: `uv run pytest tests/test_potentials.py`
- [ ] Manual check: inspect the preset's default configuration and sampled potential.

**Dependencies:** Task 1

**Files likely touched:** `src/quantum_playground/potentials.py`, `tests/test_potentials.py`

**Estimated scope:** Small

### Task 3: Implement the sparse stationary-state solver

**Description:** Assemble the second-order finite-difference Hamiltonian, compute the lowest real
eigenpairs, order them, normalize eigenstates on the grid, and return the shared result contract.

**Acceptance criteria:**

- [ ] The Hamiltonian is real, symmetric, sparse, and applies Dirichlet boundaries consistently.
- [ ] Requested low-energy eigenpairs are ordered and wavefunctions are normalized numerically.
- [ ] Invalid or failed solves produce explicit errors rather than partial results.

**Verification:**

- [ ] Focused tests: `uv run pytest tests/test_solver.py`
- [ ] Manual check: time the default infinite-well solve and record the result.

**Dependencies:** Tasks 1-2

**Files likely touched:** `src/quantum_playground/solver.py`, `tests/test_solver.py`

**Estimated scope:** Medium

### Task 4: Prove infinite-well accuracy and convergence

**Description:** Add residual, normalization, orthogonality, analytic-energy, and grid-convergence
checks so the first milestone demonstrates scientific credibility rather than only producing plots.

**Acceptance criteria:**

- [ ] The lowest states meet documented residual, normalization, and orthogonality tolerances.
- [ ] Numerical energies match the analytic infinite-well values within a stated tolerance.
- [ ] Refining the grid decreases error at the expected second-order trend over tested resolutions.

**Verification:**

- [ ] Focused tests: `uv run pytest tests/test_validation.py`
- [ ] Full suite and package build: `uv run pytest` and `uv build`

**Dependencies:** Task 3

**Files likely touched:** `src/quantum_playground/validation.py`, `tests/test_validation.py`

**Estimated scope:** Medium

### Checkpoint A: Scientific kernel

- [ ] All Phase 1 tests and quality checks pass.
- [ ] Default solve timing is recorded and assessed against the roughly 250 ms target.
- [ ] Analytic and convergence evidence is reviewed before interface expansion.

## Phase 2: First complete recruiter-facing slice

### Task 5: Build the coordinated scientific figure

**Description:** Create a pure Plotly figure builder that gives potential, energy levels,
wavefunctions, and probability density a consistent visual language without importing Streamlit.

**Acceptance criteria:**

- [ ] Potential and energy levels share a meaningful energy axis and remain distinguishable.
- [ ] A selected state can be viewed as wavefunction or probability density.
- [ ] Figure structure is deterministic and covered by selective non-pixel tests.

**Verification:**

- [ ] Focused tests: `uv run pytest tests/test_figures.py`
- [ ] Manual check: inspect default and higher-state figures at desktop width.

**Dependencies:** Tasks 3-4

**Files likely touched:** `src/quantum_playground/figures.py`, `tests/test_figures.py`

**Estimated scope:** Medium

### Task 6: Ship the guided infinite-well journey

**Description:** Replace the scaffold screen with the first end-to-end Streamlit experience:
orientation, a bounded resolution control, state selection, visualization, validation evidence,
reset behavior, and expandable numerical details.

**Acceptance criteria:**

- [ ] A first-time visitor can identify the experiment and produce a changed result within 90 seconds.
- [ ] Controls are bounded, labeled, resettable, and connected to the shared solver path.
- [ ] Initial load, recomputation, state selection, toggle, and reset pass `AppTest` coverage.

**Verification:**

- [ ] Focused tests: `uv run pytest tests/test_app.py`
- [ ] Manual check: complete the first-visit journey from a fresh session.

**Dependencies:** Task 5

**Files likely touched:** `app.py`, `tests/test_app.py`, `.streamlit/config.toml`

**Estimated scope:** Medium

### Checkpoint B: Demonstrable vertical slice

- [ ] Full quality suite and package build pass.
- [ ] Infinite-well interaction works end to end without exposing implementation jargon first.
- [ ] Browser review confirms the figure and controls are readable at the target desktop viewport.

## Phase 3: Breadth and flagship depth

### Task 7: Add the harmonic-oscillator vertical slice

**Description:** Add one bounded frequency control, analytic energy checks, a curated preset, and a
complete gallery-to-result path using the existing contracts and components.

**Acceptance criteria:**

- [ ] The preset uses `V(x) = 0.5 * omega^2 * x^2` in the documented dimensionless convention.
- [ ] Low states agree with analytic harmonic-oscillator energies within the stated domain tolerance.
- [ ] Switching experiments updates controls, explanation, result, and figure reliably.

**Verification:**

- [ ] Focused tests: `uv run pytest -k harmonic`
- [ ] Manual check: change frequency and explain the observed spacing change.

**Dependencies:** Checkpoint B

**Files likely touched:** `src/quantum_playground/potentials.py`,
`src/quantum_playground/validation.py`, `app.py`, and focused tests

**Estimated scope:** Medium

### Task 8: Add the double-well scientific slice

**Description:** Implement a symmetric quartic double-well preset with bounded, interpretable
parameters and tests for symmetry, minima, barrier behavior, and low-state splitting.

**Acceptance criteria:**

- [ ] The potential enters through the same sampled `V(x)` contract as other presets.
- [ ] Parameter changes move the intended geometric feature without creating invalid configurations.
- [ ] Tests establish expected symmetry and physically sensible low-state splitting behavior.

**Verification:**

- [ ] Focused tests: `uv run pytest -k double_well`
- [ ] Manual check: sample minimum, default, and maximum control values.

**Dependencies:** Checkpoint B

**Files likely touched:** `src/quantum_playground/potentials.py`, `tests/test_potentials.py`,
`tests/test_solver.py`

**Estimated scope:** Medium

### Task 9: Create the double-well flagship experience

**Description:** Turn the double well into the deepest interaction with an explicit splitting
metric, a meaningful baseline comparison, synchronized visual changes, and a concise tunneling
explanation.

**Acceptance criteria:**

- [ ] One or two bounded controls create an obvious and interpretable change in the lowest states.
- [ ] The current result can be compared with a stable default baseline without rerun confusion.
- [ ] State selection, density toggle, comparison, and reset survive experiment switching correctly.

**Verification:**

- [ ] Focused tests: `uv run pytest tests/test_app.py -k double_well`
- [ ] Manual check: complete and narrate the flagship interaction in under two minutes.

**Dependencies:** Task 8

**Files likely touched:** `app.py`, `src/quantum_playground/figures.py`, `tests/test_app.py`,
`tests/test_figures.py`

**Estimated scope:** Medium

### Checkpoint C: Complete scientific MVP

- [ ] All three experiments use one configuration-to-result path.
- [ ] Scientific tests and critical multi-experiment app flows pass.
- [ ] The double well is clearly the deepest and most memorable experience.

## Phase 4: Product polish and engineering hardening

### Task 10: Add progressive numerical transparency

**Description:** Present a compact trust signal in the main journey and expose residuals,
normalization, orthogonality, convergence evidence, units, and method details on demand.

**Acceptance criteria:**

- [ ] The main view communicates validity without overwhelming a non-specialist.
- [ ] Expandable details expose numerical method, grid, boundaries, tolerances, and diagnostics.
- [ ] Failed diagnostics are visible and never silently presented as trustworthy results.

**Verification:**

- [ ] Focused tests: `uv run pytest tests/test_app.py -k diagnostics`
- [ ] Manual check: compare the collapsed and expanded journeys for clarity.

**Dependencies:** Checkpoint C

**Files likely touched:** `app.py`, `tests/test_app.py`, `docs/architecture.md`

**Estimated scope:** Medium

### Task 11: Polish visual hierarchy and accessibility

**Description:** Refine typography, spacing, color, empty/loading/error states, keyboard flow, chart
labels, and responsive behavior for a deliberate desktop-first portfolio presentation.

**Acceptance criteria:**

- [ ] Primary action, result, explanation, and evidence have an obvious reading order.
- [ ] Controls have clear labels, focus behavior, contrast, and non-color-only meaning.
- [ ] Target desktop and narrow layouts have no clipped controls, unreadable labels, or chart overflow.

**Verification:**

- [ ] Automated app and figure tests pass.
- [ ] Real-browser review covers keyboard use, target desktop width, and a narrow viewport.

**Dependencies:** Task 10

**Files likely touched:** `app.py`, `.streamlit/config.toml`,
`src/quantum_playground/figures.py`, and focused tests

**Estimated scope:** Medium

### Task 12: Harden responsiveness and failure behavior

**Description:** Measure representative solves and reruns, introduce bounded caching only where it
helps, and verify that extreme allowed inputs or eigensolver failures produce actionable feedback.

**Acceptance criteria:**

- [ ] Representative local solves are approximately 250 ms or less, or the measured exception is documented.
- [ ] Typical hosted-style interactions are designed to complete in under one second.
- [ ] Cache keys are stable, cache growth is bounded, and failures do not leave stale results visible.

**Verification:**

- [ ] Focused numerical and app failure tests pass.
- [ ] A repeatable timing script or test records representative cold and warm paths.

**Dependencies:** Task 11

**Files likely touched:** `app.py`, `src/quantum_playground/solver.py`, `tests/test_solver.py`,
`tests/test_app.py`

**Estimated scope:** Medium

### Checkpoint D: Release candidate

- [ ] Full test, lint, format, and build checks pass.
- [ ] Performance measurements meet or explicitly explain the product budgets.
- [ ] The two-minute journey passes a fresh-user review with no coaching.

## Phase 5: Portfolio delivery

### Task 13: Publish the portfolio-ready release

**Description:** Finish public documentation and demo assets, deploy to Streamlit Community Cloud,
verify CI and clean-clone setup, and tag the first portfolio-ready release only after the live demo
passes acceptance.

**Acceptance criteria:**

- [ ] README leads with the live experience, a strong visual, key engineering evidence, and concise setup.
- [ ] GitHub Actions is green and a clean clone can install, test, build, and run from documented commands.
- [ ] The live app completes the primary journey, exposes no secrets, and links back to the repository.

**Verification:**

- [ ] CI passes on the release commit.
- [ ] Manual smoke test runs against the deployed URL in a real browser.
- [ ] Release checklist confirms repository metadata, screenshots, and the two-minute demo script.

**Dependencies:** Checkpoint D

**Files likely touched:** `README.md`, `assets/`, `.github/workflows/ci.yml`, deployment documentation

**Estimated scope:** Medium

### Checkpoint E: MVP complete

- [ ] Public repository and live demo are available and mutually linked.
- [ ] Product-brief success criteria are evaluated with evidence.
- [ ] Potential-composer work remains unscheduled pending post-launch evaluation.
