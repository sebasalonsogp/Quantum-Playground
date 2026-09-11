"""Curated potential presets and their validated sampling boundary."""

from dataclasses import dataclass
from math import isfinite
from numbers import Integral, Real

import numpy as np
from numpy.typing import ArrayLike

from quantum_playground.models import ExperimentId, FloatArray, SimulationConfig

_GRID_RTOL = 1e-5
_GRID_ATOL = 1e-7


@dataclass(frozen=True, slots=True)
class ParameterSpec:
    """Bounded metadata for one user-facing physical parameter."""

    key: str
    label: str
    minimum: float
    maximum: float
    default: float
    step: float
    help_text: str

    def __post_init__(self) -> None:
        if not self.key or self.key.strip() != self.key:
            raise ValueError("parameter key must be a non-empty trimmed string")
        if not self.label or not self.help_text:
            raise ValueError("parameter metadata must include a label and help text")
        values = (self.minimum, self.maximum, self.default, self.step)
        if not all(isinstance(value, Real) and not isinstance(value, bool) for value in values):
            raise ValueError("parameter bounds must be real numbers")
        if not all(isfinite(float(value)) for value in values):
            raise ValueError("parameter bounds must be finite")
        if not self.minimum < self.default < self.maximum:
            raise ValueError("parameter default must be strictly inside its bounds")
        if self.step <= 0 or self.step > self.maximum - self.minimum:
            raise ValueError("parameter step must be positive and no larger than its range")

    def validate(self, value: object) -> float:
        """Return a canonical float after validating a parameter value."""

        if isinstance(value, bool) or not isinstance(value, Real):
            raise ValueError(f"{self.key} must be a real number")
        result = float(value)
        if not isfinite(result):
            raise ValueError(f"{self.key} must be finite")
        if not self.minimum <= result <= self.maximum:
            raise ValueError(f"{self.key} must be between {self.minimum:g} and {self.maximum:g}")
        return result


@dataclass(frozen=True, slots=True)
class ExperimentPreset:
    """Deterministic scientific and explanatory defaults for one experiment."""

    experiment: ExperimentId
    title: str
    description: str
    insight: str
    default_grid_points: int
    minimum_grid_points: int
    maximum_grid_points: int
    grid_step: int
    default_eigenstate_count: int
    parameters: tuple[ParameterSpec, ...]


WIDTH = ParameterSpec(
    key="width",
    label="Well width",
    minimum=0.5,
    maximum=2.0,
    default=1.0,
    step=0.1,
    help_text="Distance between the impenetrable Dirichlet walls in dimensionless units.",
)

INFINITE_WELL_PRESET = ExperimentPreset(
    experiment=ExperimentId.INFINITE_WELL,
    title="Infinite square well",
    description="Refine the spatial grid and watch numerical energies converge to exact values.",
    insight="Its exact energy levels make the well a clear test of numerical accuracy.",
    default_grid_points=801,
    minimum_grid_points=201,
    maximum_grid_points=1_201,
    grid_step=100,
    default_eigenstate_count=6,
    parameters=(WIDTH,),
)


def _validate_grid_points(grid_points: object) -> int:
    preset = INFINITE_WELL_PRESET
    if isinstance(grid_points, bool) or not isinstance(grid_points, Integral):
        raise ValueError("grid_points must be an integer")
    result = int(grid_points)
    if not preset.minimum_grid_points <= result <= preset.maximum_grid_points:
        raise ValueError(
            "grid_points must be between "
            f"{preset.minimum_grid_points} and {preset.maximum_grid_points}"
        )
    if result % 2 == 0:
        raise ValueError("grid_points must be odd so the symmetric grid includes x = 0")
    return result


def create_infinite_well_config(
    *,
    width: float = WIDTH.default,
    grid_points: int = INFINITE_WELL_PRESET.default_grid_points,
    eigenstate_count: int = INFINITE_WELL_PRESET.default_eigenstate_count,
) -> SimulationConfig:
    """Create a validated infinite-well configuration from bounded controls."""

    canonical_width = WIDTH.validate(width)
    canonical_grid_points = _validate_grid_points(grid_points)
    half_width = canonical_width / 2.0
    return SimulationConfig(
        experiment=ExperimentId.INFINITE_WELL,
        grid_points=canonical_grid_points,
        domain=(-half_width, half_width),
        eigenstate_count=eigenstate_count,
        parameters=((WIDTH.key, canonical_width),),
    )


def _validated_grid(config: SimulationConfig, x: ArrayLike) -> FloatArray:
    grid = np.asarray(x, dtype=np.float64)
    expected_shape = (config.grid_points,)
    if grid.shape != expected_shape:
        raise ValueError(f"x must have shape {expected_shape}")
    if not np.all(np.isfinite(grid)):
        raise ValueError("x must contain only finite values")
    spacing = np.diff(grid)
    if not np.all(spacing > 0) or not np.allclose(
        spacing, spacing[0], rtol=_GRID_RTOL, atol=_GRID_ATOL
    ):
        raise ValueError("x must be a strictly increasing uniform grid")
    if not (
        np.isclose(grid[0], config.domain[0], rtol=_GRID_RTOL, atol=_GRID_ATOL)
        and np.isclose(grid[-1], config.domain[1], rtol=_GRID_RTOL, atol=_GRID_ATOL)
    ):
        raise ValueError("x must match the configured domain endpoints")
    return grid


def evaluate_potential(config: SimulationConfig, x: ArrayLike) -> FloatArray:
    """Evaluate the configured potential on a validated shared spatial grid.

    For the infinite well, the sampled interior potential is zero. Infinite walls are
    represented by the solver's homogeneous Dirichlet boundary conditions, avoiding
    non-finite values in the numerical Hamiltonian.
    """

    if config.experiment is not ExperimentId.INFINITE_WELL:
        raise ValueError(f"potential {config.experiment.value!r} is not implemented")
    if tuple(name for name, _ in config.parameters) != (WIDTH.key,):
        raise ValueError("infinite-well parameters must contain exactly 'width'")

    width = WIDTH.validate(config.parameters[0][1])
    expected_domain = (-width / 2.0, width / 2.0)
    if not np.allclose(config.domain, expected_domain, rtol=1e-12, atol=1e-12):
        raise ValueError("infinite-well domain must be centered and match its width parameter")

    _validated_grid(config, x)
    potential = np.zeros(config.grid_points, dtype=np.float64)
    potential.setflags(write=False)
    return potential


__all__ = [
    "INFINITE_WELL_PRESET",
    "ExperimentPreset",
    "ParameterSpec",
    "create_infinite_well_config",
    "evaluate_potential",
]
