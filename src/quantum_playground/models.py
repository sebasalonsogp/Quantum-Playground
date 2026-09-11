"""Typed contracts and numerical conventions shared by the application."""

from dataclasses import dataclass
from enum import StrEnum
from math import isfinite
from numbers import Integral, Real

import numpy as np
from numpy.typing import ArrayLike, NDArray

HBAR = 1.0
PARTICLE_MASS = 1.0

type FloatArray = NDArray[np.float64]
type ParameterPairs = tuple[tuple[str, float], ...]


class ExperimentId(StrEnum):
    """Stable identifiers for the curated MVP experiments."""

    INFINITE_WELL = "infinite_well"
    HARMONIC_OSCILLATOR = "harmonic_oscillator"
    DOUBLE_WELL = "double_well"


class BoundaryCondition(StrEnum):
    """Boundary conditions supported by the numerical model."""

    DIRICHLET = "dirichlet"


BOUNDARY_CONDITION = BoundaryCondition.DIRICHLET


def _finite_float(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{name} must be a real number")
    result = float(value)
    if not isfinite(result):
        raise ValueError(f"{name} must be finite")
    return result


def _readonly_float_array(values: ArrayLike, name: str, dimensions: int) -> FloatArray:
    array = np.array(values, dtype=np.float64, copy=True, order="C")
    if array.ndim != dimensions:
        raise ValueError(f"{name} must be {dimensions}-dimensional")
    if not np.all(np.isfinite(array)):
        raise ValueError(f"{name} must contain only finite values")
    array.setflags(write=False)
    return array


@dataclass(frozen=True, slots=True)
class SimulationConfig:
    """Hashable input for a one-dimensional stationary-state simulation.

    ``grid_points`` counts both domain endpoints. The endpoints obey homogeneous
    Dirichlet conditions and are excluded from the Hamiltonian's interior unknowns.
    """

    experiment: ExperimentId
    grid_points: int
    domain: tuple[float, float]
    eigenstate_count: int
    parameters: ParameterPairs = ()

    def __post_init__(self) -> None:
        if not isinstance(self.experiment, ExperimentId):
            raise ValueError("experiment must be an ExperimentId")

        if isinstance(self.grid_points, bool) or not isinstance(self.grid_points, Integral):
            raise ValueError("grid_points must be an integer")
        grid_points = int(self.grid_points)
        if grid_points < 4:
            raise ValueError("grid_points must include at least two interior points")

        if not isinstance(self.domain, tuple) or len(self.domain) != 2:
            raise ValueError("domain must be a (lower, upper) pair")
        lower = _finite_float(self.domain[0], "domain endpoints")
        upper = _finite_float(self.domain[1], "domain endpoints")
        if lower >= upper:
            raise ValueError("domain lower endpoint must be less than the upper endpoint")

        if isinstance(self.eigenstate_count, bool) or not isinstance(
            self.eigenstate_count, Integral
        ):
            raise ValueError("eigenstate_count must be an integer")
        eigenstate_count = int(self.eigenstate_count)
        if eigenstate_count < 1:
            raise ValueError("eigenstate_count must be at least one")
        if eigenstate_count >= grid_points - 2:
            raise ValueError("eigenstate_count must be smaller than the interior point count")

        if not isinstance(self.parameters, tuple):
            raise ValueError("parameters must be an immutable tuple of pairs")
        canonical_parameters: list[tuple[str, float]] = []
        names: set[str] = set()
        for pair in self.parameters:
            if not isinstance(pair, tuple) or len(pair) != 2:
                raise ValueError("each parameter must be a (name, value) pair")
            name, value = pair
            if not isinstance(name, str) or not name or name.strip() != name:
                raise ValueError("parameter name must be a non-empty trimmed string")
            if name in names:
                raise ValueError("parameter names must be unique")
            names.add(name)
            canonical_parameters.append((name, _finite_float(value, f"parameter {name}")))

        object.__setattr__(self, "grid_points", grid_points)
        object.__setattr__(self, "domain", (lower, upper))
        object.__setattr__(self, "eigenstate_count", eigenstate_count)
        object.__setattr__(self, "parameters", tuple(sorted(canonical_parameters)))

    @property
    def interior_point_count(self) -> int:
        """Number of grid points represented in the finite-difference Hamiltonian."""

        return self.grid_points - 2


@dataclass(frozen=True, slots=True, eq=False)
class NumericalDiagnostics:
    """Raw numerical trust indicators for each computed solution.

    Residual norms are relative 2-norms ``||H psi - E psi|| / ||H psi||``.
    Normalization errors are ``|integral(|psi|^2 dx) - 1|`` and the orthogonality
    error is the largest absolute entry of the overlap matrix minus the identity.
    """

    residual_norms: FloatArray
    normalization_errors: FloatArray
    orthogonality_error: float

    def __post_init__(self) -> None:
        residual_norms = _readonly_float_array(self.residual_norms, "residual_norms", 1)
        normalization_errors = _readonly_float_array(
            self.normalization_errors, "normalization_errors", 1
        )
        if np.any(residual_norms < 0) or np.any(normalization_errors < 0):
            raise ValueError("diagnostic errors must be non-negative")
        orthogonality_error = _finite_float(self.orthogonality_error, "orthogonality_error")
        if orthogonality_error < 0:
            raise ValueError("orthogonality_error must be non-negative")

        object.__setattr__(self, "residual_norms", residual_norms)
        object.__setattr__(self, "normalization_errors", normalization_errors)
        object.__setattr__(self, "orthogonality_error", orthogonality_error)


@dataclass(frozen=True, slots=True, eq=False)
class SimulationResult:
    """Ordered stationary states and the evidence needed to assess them.

    ``x`` and ``potential`` have shape ``(grid_points,)``. ``energies`` has shape
    ``(eigenstate_count,)``, and ``wavefunctions`` is state-major with shape
    ``(eigenstate_count, grid_points)``. All arrays are owned read-only ``float64`` copies.
    """

    config: SimulationConfig
    x: FloatArray
    potential: FloatArray
    energies: FloatArray
    wavefunctions: FloatArray
    diagnostics: NumericalDiagnostics
    solve_time_seconds: float

    def __post_init__(self) -> None:
        if not isinstance(self.config, SimulationConfig):
            raise ValueError("config must be a SimulationConfig")
        if not isinstance(self.diagnostics, NumericalDiagnostics):
            raise ValueError("diagnostics must be NumericalDiagnostics")

        x = _readonly_float_array(self.x, "x", 1)
        potential = _readonly_float_array(self.potential, "potential", 1)
        energies = _readonly_float_array(self.energies, "energies", 1)
        wavefunctions = _readonly_float_array(self.wavefunctions, "wavefunctions", 2)

        point_shape = (self.config.grid_points,)
        state_shape = (self.config.eigenstate_count,)
        wavefunction_shape = (self.config.eigenstate_count, self.config.grid_points)
        if x.shape != point_shape:
            raise ValueError(f"x must have shape {point_shape}")
        if potential.shape != point_shape:
            raise ValueError(f"potential must have shape {point_shape}")
        if energies.shape != state_shape:
            raise ValueError(f"energies must have shape {state_shape}")
        if wavefunctions.shape != wavefunction_shape:
            raise ValueError(f"wavefunctions must have shape {wavefunction_shape}")
        if self.diagnostics.residual_norms.shape != state_shape:
            raise ValueError(f"residual_norms must have shape {state_shape}")
        if self.diagnostics.normalization_errors.shape != state_shape:
            raise ValueError(f"normalization_errors must have shape {state_shape}")

        if not np.all(np.diff(x) > 0):
            raise ValueError("x must be strictly increasing")
        spacing = np.diff(x)
        if not np.allclose(spacing, spacing[0], rtol=1e-12, atol=1e-12):
            raise ValueError("x must be a uniform grid")
        if not (
            np.isclose(x[0], self.config.domain[0], rtol=1e-12, atol=1e-12)
            and np.isclose(x[-1], self.config.domain[1], rtol=1e-12, atol=1e-12)
        ):
            raise ValueError("x must match the configured domain endpoints")
        if np.any(np.diff(energies) < 0):
            raise ValueError("energies must be ordered in ascending order")
        if not np.allclose(wavefunctions[:, (0, -1)], 0.0, rtol=0.0, atol=1e-12):
            raise ValueError("wavefunctions must satisfy zero-value Dirichlet endpoints")

        solve_time_seconds = _finite_float(self.solve_time_seconds, "solve_time_seconds")
        if solve_time_seconds < 0:
            raise ValueError("solve_time_seconds must be non-negative")

        object.__setattr__(self, "x", x)
        object.__setattr__(self, "potential", potential)
        object.__setattr__(self, "energies", energies)
        object.__setattr__(self, "wavefunctions", wavefunctions)
        object.__setattr__(self, "solve_time_seconds", solve_time_seconds)


__all__ = [
    "BOUNDARY_CONDITION",
    "HBAR",
    "PARTICLE_MASS",
    "BoundaryCondition",
    "ExperimentId",
    "FloatArray",
    "NumericalDiagnostics",
    "ParameterPairs",
    "SimulationConfig",
    "SimulationResult",
]
