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

OMEGA = ParameterSpec(
    key="omega",
    label="Oscillator frequency ω",
    minimum=0.5,
    maximum=2.0,
    default=1.0,
    step=0.1,
    help_text="Frequency controlling the parabolic confinement and energy-level spacing.",
)

HARMONIC_OSCILLATOR_PRESET = ExperimentPreset(
    experiment=ExperimentId.HARMONIC_OSCILLATOR,
    title="Harmonic oscillator",
    description="Change the confinement strength and observe uniformly spaced energy levels.",
    insight="Its equal level spacing contrasts with the quadratic spacing of the infinite well.",
    default_grid_points=1_201,
    minimum_grid_points=401,
    maximum_grid_points=1_601,
    grid_step=200,
    default_eigenstate_count=6,
    parameters=(OMEGA,),
)

HARMONIC_DOMAIN = (-8.0, 8.0)

BARRIER_HEIGHT = ParameterSpec(
    key="barrier_height",
    label="Central barrier height V₀",
    minimum=2.5,
    maximum=8.0,
    default=4.0,
    step=0.5,
    help_text="Potential energy of the central barrier above the two minima.",
)

WELL_SEPARATION = ParameterSpec(
    key="well_separation",
    label="Distance between minima d",
    minimum=2.0,
    maximum=4.0,
    default=3.0,
    step=0.1,
    help_text="Full distance between the symmetric left and right potential minima.",
)

DOUBLE_WELL_PRESET = ExperimentPreset(
    experiment=ExperimentId.DOUBLE_WELL,
    title="Symmetric double well",
    description="Change the barrier and separation to reveal tunneling-induced state splitting.",
    insight="Its lowest even and odd states form a tunneling pair separated by a small energy gap.",
    default_grid_points=1_201,
    minimum_grid_points=401,
    maximum_grid_points=1_601,
    grid_step=200,
    default_eigenstate_count=6,
    parameters=(BARRIER_HEIGHT, WELL_SEPARATION),
)

DOUBLE_WELL_DOMAIN = (-6.0, 6.0)


def _validate_grid_points(grid_points: object, preset: ExperimentPreset) -> int:
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
    canonical_grid_points = _validate_grid_points(grid_points, INFINITE_WELL_PRESET)
    half_width = canonical_width / 2.0
    return SimulationConfig(
        experiment=ExperimentId.INFINITE_WELL,
        grid_points=canonical_grid_points,
        domain=(-half_width, half_width),
        eigenstate_count=eigenstate_count,
        parameters=((WIDTH.key, canonical_width),),
    )


def create_harmonic_oscillator_config(
    *,
    omega: float = OMEGA.default,
    grid_points: int = HARMONIC_OSCILLATOR_PRESET.default_grid_points,
    eigenstate_count: int = HARMONIC_OSCILLATOR_PRESET.default_eigenstate_count,
) -> SimulationConfig:
    """Create a validated harmonic-oscillator configuration."""

    canonical_omega = OMEGA.validate(omega)
    canonical_grid_points = _validate_grid_points(grid_points, HARMONIC_OSCILLATOR_PRESET)
    return SimulationConfig(
        experiment=ExperimentId.HARMONIC_OSCILLATOR,
        grid_points=canonical_grid_points,
        domain=HARMONIC_DOMAIN,
        eigenstate_count=eigenstate_count,
        parameters=((OMEGA.key, canonical_omega),),
    )


def create_double_well_config(
    *,
    barrier_height: float = BARRIER_HEIGHT.default,
    well_separation: float = WELL_SEPARATION.default,
    grid_points: int = DOUBLE_WELL_PRESET.default_grid_points,
    eigenstate_count: int = DOUBLE_WELL_PRESET.default_eigenstate_count,
) -> SimulationConfig:
    """Create a validated symmetric quartic double-well configuration."""

    canonical_barrier = BARRIER_HEIGHT.validate(barrier_height)
    canonical_separation = WELL_SEPARATION.validate(well_separation)
    canonical_grid_points = _validate_grid_points(grid_points, DOUBLE_WELL_PRESET)
    return SimulationConfig(
        experiment=ExperimentId.DOUBLE_WELL,
        grid_points=canonical_grid_points,
        domain=DOUBLE_WELL_DOMAIN,
        eigenstate_count=eigenstate_count,
        parameters=(
            (BARRIER_HEIGHT.key, canonical_barrier),
            (WELL_SEPARATION.key, canonical_separation),
        ),
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

    grid = _validated_grid(config, x)
    parameter_names = tuple(name for name, _ in config.parameters)
    if config.experiment is ExperimentId.INFINITE_WELL:
        if parameter_names != (WIDTH.key,):
            raise ValueError("infinite-well parameters must contain exactly 'width'")
        width = WIDTH.validate(config.parameters[0][1])
        expected_domain = (-width / 2.0, width / 2.0)
        if not np.allclose(config.domain, expected_domain, rtol=1e-12, atol=1e-12):
            raise ValueError("infinite-well domain must be centered and match its width parameter")
        potential = np.zeros(config.grid_points, dtype=np.float64)
    elif config.experiment is ExperimentId.HARMONIC_OSCILLATOR:
        if parameter_names != (OMEGA.key,):
            raise ValueError("harmonic-oscillator parameters must contain exactly 'omega'")
        omega = OMEGA.validate(config.parameters[0][1])
        if not np.allclose(config.domain, HARMONIC_DOMAIN, rtol=1e-12, atol=1e-12):
            raise ValueError("harmonic-oscillator domain must match the preset finite domain")
        potential = 0.5 * omega**2 * grid**2
    elif config.experiment is ExperimentId.DOUBLE_WELL:
        expected_parameters = (BARRIER_HEIGHT.key, WELL_SEPARATION.key)
        if parameter_names != expected_parameters:
            raise ValueError(
                "double-well parameters must contain exactly 'barrier_height' and 'well_separation'"
            )
        barrier_height = BARRIER_HEIGHT.validate(config.parameters[0][1])
        well_separation = WELL_SEPARATION.validate(config.parameters[1][1])
        if not np.allclose(config.domain, DOUBLE_WELL_DOMAIN, rtol=1e-12, atol=1e-12):
            raise ValueError("double-well domain must match the preset finite domain")

        # Reparameterized from lambda * (x^2 - a^2)^2 so the controls directly
        # set V(0) and the full distance 2a between minima.
        # Source: https://web.physics.ucsb.edu/~davidgrabovsky/files-teaching/Double%20Well%20Problems.pdf
        potential = barrier_height * ((2.0 * grid / well_separation) ** 2 - 1.0) ** 2
    else:
        raise ValueError(f"potential {config.experiment.value!r} is not implemented")

    potential.setflags(write=False)
    return potential


__all__ = [
    "BARRIER_HEIGHT",
    "DOUBLE_WELL_DOMAIN",
    "DOUBLE_WELL_PRESET",
    "HARMONIC_DOMAIN",
    "HARMONIC_OSCILLATOR_PRESET",
    "INFINITE_WELL_PRESET",
    "OMEGA",
    "WELL_SEPARATION",
    "ExperimentPreset",
    "ParameterSpec",
    "create_double_well_config",
    "create_harmonic_oscillator_config",
    "create_infinite_well_config",
    "evaluate_potential",
]
