"""Sparse finite-difference solver for one-dimensional stationary states."""

from time import perf_counter

import numpy as np
from numpy.typing import ArrayLike
from scipy.sparse import csr_array, diags_array
from scipy.sparse.linalg import ArpackError, ArpackNoConvergence, eigsh

from quantum_playground.models import (
    HBAR,
    PARTICLE_MASS,
    FloatArray,
    NumericalDiagnostics,
    SimulationConfig,
    SimulationResult,
)
from quantum_playground.potentials import evaluate_potential

_GRID_RTOL = 1e-12
_GRID_ATOL = 1e-12


class SolverError(RuntimeError):
    """Raised when a valid simulation cannot produce a complete solution."""


def _require_config(config: object) -> SimulationConfig:
    if not isinstance(config, SimulationConfig):
        raise ValueError("config must be a SimulationConfig")
    return config


def build_spatial_grid(config: SimulationConfig) -> FloatArray:
    """Return the configured uniform grid, including both Dirichlet endpoints."""

    canonical_config = _require_config(config)
    x = np.linspace(
        *canonical_config.domain,
        canonical_config.grid_points,
        dtype=np.float64,
    )
    x.setflags(write=False)
    return x


def _validated_samples(
    config: SimulationConfig,
    x: ArrayLike,
    potential: ArrayLike,
) -> tuple[FloatArray, FloatArray]:
    grid = np.asarray(x, dtype=np.float64)
    values = np.asarray(potential, dtype=np.float64)
    expected_shape = (config.grid_points,)

    if grid.shape != expected_shape:
        raise ValueError(f"x must have shape {expected_shape}")
    if not np.all(np.isfinite(grid)):
        raise ValueError("x must contain only finite values")
    spacing = np.diff(grid)
    if not np.all(spacing > 0.0) or not np.allclose(
        spacing,
        spacing[0],
        rtol=_GRID_RTOL,
        atol=_GRID_ATOL,
    ):
        raise ValueError("x must be a strictly increasing uniform grid")
    if not (
        np.isclose(grid[0], config.domain[0], rtol=_GRID_RTOL, atol=_GRID_ATOL)
        and np.isclose(grid[-1], config.domain[1], rtol=_GRID_RTOL, atol=_GRID_ATOL)
    ):
        raise ValueError("x must match the configured domain endpoints")

    if values.shape != expected_shape:
        raise ValueError(f"potential must have shape {expected_shape}")
    if not np.all(np.isfinite(values)):
        raise ValueError("potential must contain only finite values")
    return grid, values


def build_hamiltonian(
    config: SimulationConfig,
    x: ArrayLike,
    potential: ArrayLike,
) -> csr_array:
    """Assemble the real symmetric interior Hamiltonian in CSR format."""

    canonical_config = _require_config(config)
    grid, potential_values = _validated_samples(canonical_config, x, potential)
    interior_count = canonical_config.interior_point_count
    dx = float(grid[1] - grid[0])
    kinetic_scale = HBAR**2 / (2.0 * PARTICLE_MASS * dx**2)
    main_diagonal = 2.0 * kinetic_scale + potential_values[1:-1]
    off_diagonal = np.full(interior_count - 1, -kinetic_scale, dtype=np.float64)

    # SciPy recommends diags_array for new sparse-array code.
    # Source: https://docs.scipy.org/doc/scipy/reference/generated/scipy.sparse.diags_array.html
    return diags_array(
        (off_diagonal, main_diagonal, off_diagonal),
        offsets=(-1, 0, 1),
        shape=(interior_count, interior_count),
        format="csr",
        dtype=np.float64,
    )


def _lowest_eigenpairs(
    hamiltonian: csr_array,
    state_count: int,
) -> tuple[FloatArray, FloatArray]:
    starting_vector = np.linspace(1.0, 2.0, hamiltonian.shape[0], dtype=np.float64)
    try:
        # ``SA`` selects the smallest algebraic eigenvalues of a real symmetric matrix.
        # Source: https://docs.scipy.org/doc/scipy/reference/generated/scipy.sparse.linalg.eigsh.html
        energies, eigenvectors = eigsh(
            hamiltonian,
            k=state_count,
            which="SA",
            v0=starting_vector,
        )
    except ArpackNoConvergence as error:
        # ARPACK exposes partial results on this exception; the application deliberately
        # rejects them so plots never mix complete and incomplete states.
        raise SolverError("stationary-state solve did not converge") from error
    except ArpackError as error:
        raise SolverError("stationary-state eigensolver failed") from error

    expected_vector_shape = (hamiltonian.shape[0], state_count)
    if energies.shape != (state_count,) or eigenvectors.shape != expected_vector_shape:
        raise SolverError("eigensolver returned an incomplete result")
    if not np.all(np.isfinite(energies)) or not np.all(np.isfinite(eigenvectors)):
        raise SolverError("eigensolver returned non-finite values")

    order = np.argsort(energies, kind="stable")
    return (
        np.asarray(energies[order], dtype=np.float64),
        np.asarray(eigenvectors[:, order], dtype=np.float64),
    )


def _normalized_wavefunctions(
    eigenvectors: FloatArray,
    x: FloatArray,
) -> FloatArray:
    state_count = eigenvectors.shape[1]
    wavefunctions = np.zeros((state_count, x.size), dtype=np.float64)
    wavefunctions[:, 1:-1] = eigenvectors.T

    # Source: https://numpy.org/doc/stable/reference/generated/numpy.trapezoid.html
    norms = np.trapezoid(wavefunctions**2, x, axis=1)
    if not np.all(np.isfinite(norms)) or np.any(norms <= 0.0):
        raise SolverError("eigensolver returned states that cannot be normalized")
    wavefunctions /= np.sqrt(norms)[:, np.newaxis]

    for wavefunction in wavefunctions:
        anchor = int(np.argmax(np.abs(wavefunction)))
        if wavefunction[anchor] < 0.0:
            wavefunction *= -1.0
    return wavefunctions


def _diagnostics(
    hamiltonian: csr_array,
    energies: FloatArray,
    wavefunctions: FloatArray,
    x: FloatArray,
) -> NumericalDiagnostics:
    interior_vectors = wavefunctions[:, 1:-1].T
    hamiltonian_vectors = hamiltonian @ interior_vectors
    residuals = hamiltonian_vectors - interior_vectors * energies[np.newaxis, :]
    residual_scales = np.maximum(
        np.linalg.norm(hamiltonian_vectors, axis=0),
        np.finfo(np.float64).tiny,
    )
    residual_norms = np.linalg.norm(residuals, axis=0) / residual_scales

    norms = np.trapezoid(wavefunctions**2, x, axis=1)
    normalization_errors = np.abs(norms - 1.0)
    overlap = np.trapezoid(
        wavefunctions[:, np.newaxis, :] * wavefunctions[np.newaxis, :, :],
        x,
        axis=2,
    )
    orthogonality_error = float(np.max(np.abs(overlap - np.eye(energies.size))))
    return NumericalDiagnostics(
        residual_norms=residual_norms,
        normalization_errors=normalization_errors,
        orthogonality_error=orthogonality_error,
    )


def solve(config: SimulationConfig) -> SimulationResult:
    """Return a complete ordered and normalized stationary-state solution."""

    canonical_config = _require_config(config)
    start_time = perf_counter()
    x = build_spatial_grid(canonical_config)
    potential = evaluate_potential(canonical_config, x)
    hamiltonian = build_hamiltonian(canonical_config, x, potential)
    energies, eigenvectors = _lowest_eigenpairs(
        hamiltonian,
        canonical_config.eigenstate_count,
    )
    wavefunctions = _normalized_wavefunctions(eigenvectors, x)
    diagnostics = _diagnostics(hamiltonian, energies, wavefunctions, x)

    return SimulationResult(
        config=canonical_config,
        x=x,
        potential=potential,
        energies=energies,
        wavefunctions=wavefunctions,
        diagnostics=diagnostics,
        solve_time_seconds=perf_counter() - start_time,
    )


__all__ = ["SolverError", "build_hamiltonian", "build_spatial_grid", "solve"]
