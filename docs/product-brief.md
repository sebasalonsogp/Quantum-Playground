# Quantum Playground Product Brief

## Objective

Build a focused interactive laboratory that demonstrates an ability to translate a mathematical
model into trustworthy scientific software and present it through an approachable product
experience.

The portfolio takeaway is:

> This developer can implement rigorous numerical methods, validate the results, and turn
> difficult technical material into an effective interactive experience.

## Audience

1. **Recruiter or hiring manager:** Recognizes a polished, technically ambitious project quickly.
2. **Curious technical visitor:** Explores a quantum phenomenon without writing code.
3. **Technical reviewer:** Inspects the numerical method, validation, architecture, and tests.

## Problem statement

How might we let a time-constrained portfolio reviewer discover, within two minutes, that the
creator can build rigorous scientific software through a polished quantum experiment that exposes
both physical behavior and numerical evidence?

## Product direction

Quantum Playground combines:

- **Curated breadth:** Three canonical experiments establish that the solver is reusable.
- **One deep flagship interaction:** The double well provides the memorable centerpiece.
- **Numerical transparency:** Validation and diagnostics prove that the visuals are trustworthy.

The core interaction is:

`choose an experiment → change one parameter → observe a change → understand it → verify it`

## MVP

### Experiments

- Infinite square well for analytic validation and convergence.
- Harmonic oscillator for a second canonical system.
- Double well for tunneling-driven state splitting and the flagship interaction.

### Scientific capabilities

- Uniform one-dimensional grid with explicit Dirichlet boundaries.
- Dimensionless units with `ℏ = m = 1` stated in the interface.
- Second-order finite-difference Hamiltonian.
- Real symmetric sparse matrix and the lowest few eigenpairs.
- Ordered, normalized eigenstates.
- Residual, normalization, and orthogonality diagnostics.
- Infinite-well analytic comparison and grid-convergence evidence.

### Product capabilities

- Experiment gallery with strong presets.
- One or two bounded controls per experiment.
- Coordinated potential, energy, wavefunction, and probability-density visualization.
- Eigenstate selection and wavefunction/density toggle.
- Reset behavior, double-well baseline comparison, and an interactive tunneling-cycle scrubber.
- Concise physical explanation and expandable numerical details.
- Deliberate desktop-first visual design.

## Success criteria

- A visitor understands the project within 30 seconds.
- A visitor produces a meaningful result within 90 seconds.
- The double-well controls create an obvious and interpretable change.
- Analytic error decreases as the infinite-well grid is refined.
- Eigenstates meet documented normalization, orthogonality, and residual tolerances.
- Typical local solves take roughly 250 ms or less.
- Hosted interactions normally update in under one second.
- Numerical behavior and critical application flows have deterministic automated tests.

## Key assumptions to validate

- The coordinated visualization is understandable without deep quantum-mechanics knowledge.
- Three experiments establish breadth without weakening the flagship experience.
- Streamlit remains responsive at 500–1,000 grid points and roughly six eigenpairs.
- Numerical details provide credibility without overwhelming the initial interaction.

## Not in the MVP

- Potential composer or arbitrary mathematical expressions.
- Time-dependent, two-dimensional, or three-dimensional systems.
- User accounts, saved sessions, database, or separate API service.
- React frontend, background workers, GPU, or distributed infrastructure.
- Full instructional curriculum or mobile-first optimization.

## Future expansion

The potential composer remains the preferred future extension. It must produce the same sampled
`V(x)` representation as a preset, preserving one numerical path:

`preset or composer → V(x) → Hamiltonian → eigenpairs → diagnostics → visualization`

The drawing interface, interpolation, and validation rules will only enter scope after the MVP is
complete and its interaction quality has been evaluated.

## First milestone

Implement and validate the infinite square well before building the full interface. The milestone
must produce low-energy eigenpairs, analytic error measurements, convergence evidence, and solver
timing at the intended default grid size.
