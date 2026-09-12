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

- [x] The well uses the documented domain and boundary convention.
- [x] Preset metadata includes bounded defaults and concise user-facing explanatory text.
- [x] Potential output has the expected shape, type, and finite interior values.

**Verification:**

- [x] Focused tests: `uv run pytest tests/test_potentials.py`
- [x] Manual check: inspect the preset's default configuration and sampled potential.

**Dependencies:** Task 1

**Files likely touched:** `src/quantum_playground/potentials.py`, `tests/test_potentials.py`

**Estimated scope:** Small

### Task 3: Implement the sparse stationary-state solver

**Description:** Assemble the second-order finite-difference Hamiltonian, compute the lowest real
eigenpairs, order them, normalize eigenstates on the grid, and return the shared result contract.

**Acceptance criteria:**

- [x] The Hamiltonian is real, symmetric, sparse, and applies Dirichlet boundaries consistently.
- [x] Requested low-energy eigenpairs are ordered and wavefunctions are normalized numerically.
- [x] Invalid or failed solves produce explicit errors rather than partial results.

**Verification:**

- [x] Focused tests: `uv run pytest tests/test_solver.py`
- [x] Manual check: time the default infinite-well solve and record the result.

**Recorded timing (2026-09-11):** Five local Windows runs with CPython 3.12 and SciPy 1.18.1
completed the default 801-point, six-state solve in 194.30–201.05 ms (195.07 ms median). The
largest relative residual in the final run was `3.85e-10`.

**Dependencies:** Tasks 1-2

**Files likely touched:** `src/quantum_playground/solver.py`, `tests/test_solver.py`

**Estimated scope:** Medium

### Task 4: Prove infinite-well accuracy and convergence

**Description:** Add residual, normalization, orthogonality, analytic-energy, and grid-convergence
checks so the first milestone demonstrates scientific credibility rather than only producing plots.

**Acceptance criteria:**

- [x] The lowest states meet documented residual, normalization, and orthogonality tolerances.
- [x] Numerical energies match the analytic infinite-well values within a stated tolerance.
- [x] Refining the grid decreases error at the expected second-order trend over tested resolutions.

**Verification:**

- [x] Focused tests: `uv run pytest tests/test_validation.py`
- [x] Full suite and package build: `uv run pytest` and `uv build`

**Recorded evidence (2026-09-11):** The default six-state solve had a maximum relative energy
error of `4.63e-5`, relative residual of `3.85e-10`, normalization error of `4.44e-16`, and
orthogonality error of `6.49e-15`. Ground-state refinement over 201, 401, and 801 points produced
relative errors of `2.06e-5`, `5.14e-6`, and `1.29e-6`, with observed orders `1.99999` and
`2.00000`.

**Dependencies:** Task 3

**Files likely touched:** `src/quantum_playground/validation.py`, `tests/test_validation.py`

**Estimated scope:** Medium

### Checkpoint A: Scientific kernel

- [x] All Phase 1 tests and quality checks pass.
- [x] Default solve timing is recorded and assessed against the roughly 250 ms target.
- [x] Analytic and convergence evidence is reviewed before interface expansion.

## Phase 2: First complete recruiter-facing slice

### Task 5: Build the coordinated scientific figure

**Description:** Create a pure Plotly figure builder that gives potential, energy levels,
wavefunctions, and probability density a consistent visual language without importing Streamlit.

**Acceptance criteria:**

- [x] Potential and energy levels share a meaningful energy axis and remain distinguishable.
- [x] A selected state can be viewed as wavefunction or probability density.
- [x] Figure structure is deterministic and covered by selective non-pixel tests.

**Verification:**

- [x] Focused tests: `uv run pytest tests/test_figures.py`
- [x] Manual check: inspected the default wavefunction and a higher-state probability density at
  1264 × 712 on 2026-09-11. Labels, nodes, energy levels, and boundaries remained readable; the
  default Plotly zero-axis line was disabled because it could be mistaken for a physical boundary.

**Dependencies:** Tasks 3-4

**Files likely touched:** `src/quantum_playground/figures.py`, `tests/test_figures.py`

**Estimated scope:** Medium

### Task 6: Ship the guided infinite-well journey

**Description:** Replace the scaffold screen with the first end-to-end Streamlit experience:
orientation, a bounded resolution control, state selection, visualization, validation evidence,
reset behavior, and expandable numerical details.

**Acceptance criteria:**

- [x] A first-time visitor can identify the experiment and produce a changed result within 90 seconds.
- [x] Controls are bounded, labeled, resettable, and connected to the shared solver path.
- [x] Initial load, recomputation, state selection, toggle, and reset pass `AppTest` coverage.

**Verification:**

- [x] Focused tests: `uv run pytest tests/test_app.py`
- [x] Manual check: completed the first-visit journey at 1264 × 712 on 2026-09-11,
  including state selection, density switching, width recomputation, numerical-details review,
  and reset.

**Dependencies:** Task 5

**Files likely touched:** `app.py`, `tests/test_app.py`, `.streamlit/config.toml`

**Estimated scope:** Medium

### Checkpoint B: Demonstrable vertical slice

- [x] Full quality suite and package build pass.
- [x] Infinite-well interaction works end to end without exposing implementation jargon first.
- [x] Browser review confirms the figure and controls are readable at the target desktop viewport.

## Phase 3: Breadth and flagship depth

### Task 7: Add the harmonic-oscillator vertical slice

**Description:** Add one bounded frequency control, analytic energy checks, a curated preset, and a
complete gallery-to-result path using the existing contracts and components.

**Acceptance criteria:**

- [x] The preset uses `V(x) = 0.5 * omega^2 * x^2` in the documented dimensionless convention.
- [x] Low states agree with analytic harmonic-oscillator energies within the stated domain tolerance.
- [x] Switching experiments updates controls, explanation, result, and figure reliably.

**Verification:**

- [x] Focused tests: `uv run pytest -k harmonic`
- [x] Manual check: changed frequency from `omega = 1.0` to `omega = 2.0` in a real browser on
  2026-09-11. The ground-state energy doubled from approximately `0.5` to `1.0`, every adjacent
  level gap doubled from `1.0` to `2.0`, and the state contracted toward the potential minimum.

**Recorded evidence (2026-09-11):** On the fixed `[-8, 8]` domain with 1,201 points, maximum
relative energy errors across the six displayed states were `3.073e-5`, `6.162e-5`, and
`1.232e-4` at `omega = 0.5`, `1.0`, and `2.0`, respectively. All remain below the stated
`1.5e-4` tolerance.

**Dependencies:** Checkpoint B

**Files likely touched:** `src/quantum_playground/potentials.py`,
`src/quantum_playground/validation.py`, `app.py`, and focused tests

**Estimated scope:** Medium

### Task 8: Add the double-well scientific slice

**Description:** Implement a symmetric quartic double-well preset with bounded, interpretable
parameters and tests for symmetry, minima, barrier behavior, and low-state splitting.

**Acceptance criteria:**

- [x] The potential enters through the same sampled `V(x)` contract as other presets.
- [x] Parameter changes move the intended geometric feature without creating invalid configurations.
- [x] Tests establish expected symmetry and physically sensible low-state splitting behavior.

**Verification:**

- [x] Focused tests: `uv run pytest -k double_well`
- [x] Manual check: sample minimum, default, and maximum control values.

**Recorded evidence (2026-09-11):** With `V(x) = V0 * ((2x / d)^2 - 1)^2` on `[-6, 6]`,
the minimum (`V0 = 2.5`, `d = 2.0`), default (`V0 = 4.0`, `d = 3.0`), and maximum
(`V0 = 8.0`, `d = 4.0`) samples placed their minima at `+/-1.0`, `+/-1.5`, and `+/-2.0`
and reproduced their requested central barriers. Their lowest-state splittings were `0.631067`,
`0.068624`, and `0.000758`, respectively; both states remained below the barrier and maximum
relative residuals were at most `1.41e-11`. Solve times were 69.2–112.0 ms locally.

**Dependencies:** Checkpoint B

**Files likely touched:** `src/quantum_playground/potentials.py`, `tests/test_potentials.py`,
`tests/test_solver.py`

**Estimated scope:** Medium

### Task 9: Create the double-well flagship experience

**Description:** Turn the double well into the deepest interaction with an explicit splitting
metric, a meaningful baseline comparison, synchronized visual changes, and a concise tunneling
explanation.

**Acceptance criteria:**

- [x] One or two bounded controls create an obvious and interpretable change in the lowest states.
- [x] The current result can be compared with a stable default baseline without rerun confusion.
- [x] State selection, density toggle, comparison, and reset survive experiment switching correctly.

**Verification:**

- [x] Focused tests: `uv run pytest tests/test_app.py -k double_well`
- [x] Manual check: complete and narrate the flagship interaction in under two minutes.

**Recorded evidence (2026-09-11):** At a 985 × 983 browser viewport, the direct journey changed
the default splitting from `0.068624` to `0.000758` (`-98.9%`) at `V0 = 8.0` and `d = 4.0`,
selected the odd second state, switched to probability density, removed the fixed comparison, and
restored every default. Solid current traces and muted reference traces remained distinguishable,
the chart title and legend did not overlap, all controls exposed accessible names, and the browser
console remained clean. The interaction requires seven direct actions and fits a two-minute demo.

**Dependencies:** Task 8

**Files likely touched:** `app.py`, `src/quantum_playground/figures.py`, `tests/test_app.py`,
`tests/test_figures.py`

**Estimated scope:** Medium

### Checkpoint C: Complete scientific MVP

- [x] All three experiments use one configuration-to-result path.
- [x] Scientific tests and critical multi-experiment app flows pass.
- [x] The double well is clearly the deepest and most memorable experience.

## Phase 4: Product polish and engineering hardening

### Task 10: Add progressive numerical transparency

**Description:** Present a compact trust signal in the main journey and expose residuals,
normalization, orthogonality, convergence evidence, units, and method details on demand.

**Acceptance criteria:**

- [x] The main view communicates validity without overwhelming a non-specialist.
- [x] Expandable details expose numerical method, grid, boundaries, tolerances, and diagnostics.
- [x] Failed diagnostics are visible and never silently presented as trustworthy results.

**Verification:**

- [x] Focused tests: `uv run pytest tests/test_app.py -k diagnostics`
- [x] Manual check: compare the collapsed and expanded journeys for clarity.

**Dependencies:** Checkpoint C

**Files likely touched:** `app.py`, `tests/test_app.py`, `docs/architecture.md`

**Estimated scope:** Medium

### Task 11: Polish visual hierarchy and accessibility

**Description:** Refine typography, spacing, color, empty/loading/error states, keyboard flow, chart
labels, and responsive behavior for a deliberate desktop-first portfolio presentation.

**Acceptance criteria:**

- [x] Primary action, result, explanation, and evidence have an obvious reading order.
- [x] Controls have clear labels, focus behavior, contrast, and non-color-only meaning.
- [x] Target desktop and narrow layouts have no clipped controls, unreadable labels, or chart overflow.

**Verification:**

- [x] Automated app and figure tests pass.
- [x] Real-browser review covers keyboard use, target desktop width, and a narrow viewport.

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
