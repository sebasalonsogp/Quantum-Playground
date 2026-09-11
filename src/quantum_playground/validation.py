"""Scientific validation evidence for curated quantum experiments."""

from collections.abc import Sequence
from dataclasses import dataclass
from math import isfinite
from numbers import Integral, Real

import numpy as np
from numpy.typing import ArrayLike

from quantum_playground.models import (
    HBAR,
    PARTICLE_MASS,
    ExperimentId,
    FloatArray,
    SimulationConfig,
    SimulationResult,
)
from quantum_playground.potentials import WIDTH

MAX_RELATIVE_RESIDUAL = 1e-8
MAX_NORMALIZATION_ERROR = 1e-12
MAX_ORTHOGONALITY_ERROR = 1e-12
MAX_RELATIVE_ENERGY_ERROR = 1e-4
SECOND_ORDER_TARGET = 2.0
SECOND_ORDER_TOLERANCE = 0.1


def _readonly_vector(values: ArrayLike, name: str) -> FloatArray:
    vector = np.array(values, dtype=np.float64, copy=True)
    if vector.ndim != 1 or vector.size == 0:
        raise ValueError(f"{name} must be a non-empty one-dimensional array")
    if not np.all(np.isfinite(vector)):
        raise ValueError(f"{name} must contain only finite values")
    vector.setflags(write=False)
    return vector


def _nonnegative_float(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{name} must be a real number")
    result = float(value)
    if not isfinite(result) or result < 0.0:
        raise ValueError(f"{name} must be finite and non-negative")
    return result


@dataclass(frozen=True, slots=True, eq=False)
class ValidationReport:
    """Analytic and numerical trust evidence for one infinite-well solve."""

    analytic_energies: FloatArray
    relative_energy_errors: FloatArray
    maximum_relative_residual: float
    maximum_normalization_error: float
    orthogonality_error: float

    def __post_init__(self) -> None:
        analytic_energies = _readonly_vector(self.analytic_energies, "analytic_energies")
        relative_energy_errors = _readonly_vector(
            self.relative_energy_errors,
            "relative_energy_errors",
        )
        if analytic_energies.shape != relative_energy_errors.shape:
            raise ValueError("analytic energies and relative errors must have matching shapes")
        if np.any(analytic_energies <= 0.0) or np.any(relative_energy_errors < 0.0):
            raise ValueError("energies must be positive and relative errors non-negative")

        object.__setattr__(self, "analytic_energies", analytic_energies)
        object.__setattr__(self, "relative_energy_errors", relative_energy_errors)
        object.__setattr__(
            self,
            "maximum_relative_residual",
            _nonnegative_float(self.maximum_relative_residual, "maximum_relative_residual"),
        )
        object.__setattr__(
            self,
            "maximum_normalization_error",
            _nonnegative_float(self.maximum_normalization_error, "maximum_normalization_error"),
        )
        object.__setattr__(
            self,
            "orthogonality_error",
            _nonnegative_float(self.orthogonality_error, "orthogonality_error"),
        )

    @property
    def maximum_relative_energy_error(self) -> float:
        return float(np.max(self.relative_energy_errors))

    @property
    def energy_accurate(self) -> bool:
        return self.maximum_relative_energy_error <= MAX_RELATIVE_ENERGY_ERROR

    @property
    def residuals_accurate(self) -> bool:
        return self.maximum_relative_residual <= MAX_RELATIVE_RESIDUAL

    @property
    def normalization_accurate(self) -> bool:
        return self.maximum_normalization_error <= MAX_NORMALIZATION_ERROR

    @property
    def orthogonality_accurate(self) -> bool:
        return self.orthogonality_error <= MAX_ORTHOGONALITY_ERROR

    @property
    def passed(self) -> bool:
        return all(
            (
                self.energy_accurate,
                self.residuals_accurate,
                self.normalization_accurate,
                self.orthogonality_accurate,
            )
        )


@dataclass(frozen=True, slots=True, eq=False)
class ConvergenceReport:
    """Relative energy errors and observed orders across refined grids.

    Source for the centered second-derivative stencil's ``O(h^2)`` error:
    https://math.mit.edu/icg/resources/teaching/18.085-spring2015/SecondOrder.pdf
    """

    grid_spacings: FloatArray
    relative_energy_errors: FloatArray
    observed_orders: FloatArray

    def __post_init__(self) -> None:
        grid_spacings = _readonly_vector(self.grid_spacings, "grid_spacings")
        relative_energy_errors = _readonly_vector(
            self.relative_energy_errors,
            "relative_energy_errors",
        )
        observed_orders = _readonly_vector(self.observed_orders, "observed_orders")
        if grid_spacings.shape != relative_energy_errors.shape:
            raise ValueError("grid spacings and relative errors must have matching shapes")
        if observed_orders.size != grid_spacings.size - 1:
            raise ValueError("observed_orders must compare each adjacent grid pair")
        if np.any(grid_spacings <= 0.0) or np.any(relative_energy_errors <= 0.0):
            raise ValueError("grid spacings and relative errors must be positive")
        if not np.all(np.diff(grid_spacings) < 0.0):
            raise ValueError("grid spacings must be ordered coarse-to-fine")

        object.__setattr__(self, "grid_spacings", grid_spacings)
        object.__setattr__(self, "relative_energy_errors", relative_energy_errors)
        object.__setattr__(self, "observed_orders", observed_orders)

    @property
    def errors_decrease(self) -> bool:
        return bool(np.all(np.diff(self.relative_energy_errors) < 0.0))

    @property
    def is_second_order(self) -> bool:
        return bool(
            np.all(np.abs(self.observed_orders - SECOND_ORDER_TARGET) <= SECOND_ORDER_TOLERANCE)
        )

    @property
    def passed(self) -> bool:
        return self.errors_decrease and self.is_second_order


def _infinite_well_width(config: SimulationConfig) -> float:
    if not isinstance(config, SimulationConfig):
        raise ValueError("config must be a SimulationConfig")
    if config.experiment is not ExperimentId.INFINITE_WELL:
        raise ValueError("validation requires an infinite-well configuration")
    if tuple(name for name, _ in config.parameters) != (WIDTH.key,):
        raise ValueError("infinite-well parameters must contain exactly 'width'")

    width = WIDTH.validate(config.parameters[0][1])
    expected_domain = (-width / 2.0, width / 2.0)
    if not np.allclose(config.domain, expected_domain, rtol=1e-12, atol=1e-12):
        raise ValueError("infinite-well domain must be centered and match its width parameter")
    return width


def infinite_well_analytic_energies(config: SimulationConfig) -> FloatArray:
    """Return exact infinite-well energies for the configured state count.

    The formula is ``E_n = hbar^2 pi^2 n^2 / (2 m L^2)`` for positive integer
    ``n`` and well width ``L``.

    Source: https://ocw.mit.edu/courses/8-04-quantum-physics-i-spring-2016/resources/mit8_04s16_lecnotes11/
    """

    width = _infinite_well_width(config)
    state_numbers = np.arange(1, config.eigenstate_count + 1, dtype=np.float64)
    energies = (HBAR * np.pi * state_numbers) ** 2 / (2.0 * PARTICLE_MASS * width**2)
    energies.setflags(write=False)
    return energies


def validate_infinite_well(result: SimulationResult) -> ValidationReport:
    """Compare one solution with exact energies and documented numerical tolerances."""

    if not isinstance(result, SimulationResult):
        raise ValueError("result must be a SimulationResult")
    analytic_energies = infinite_well_analytic_energies(result.config)
    relative_energy_errors = np.abs(result.energies - analytic_energies) / analytic_energies
    diagnostics = result.diagnostics
    return ValidationReport(
        analytic_energies=analytic_energies,
        relative_energy_errors=relative_energy_errors,
        maximum_relative_residual=float(np.max(diagnostics.residual_norms)),
        maximum_normalization_error=float(np.max(diagnostics.normalization_errors)),
        orthogonality_error=diagnostics.orthogonality_error,
    )


def assess_infinite_well_convergence(
    results: Sequence[SimulationResult],
    *,
    state_index: int = 0,
) -> ConvergenceReport:
    """Measure energy-error order across matching coarse-to-fine solutions."""

    result_sequence = tuple(results)
    if len(result_sequence) < 3:
        raise ValueError("convergence assessment requires at least three results")
    if isinstance(state_index, bool) or not isinstance(state_index, Integral):
        raise ValueError("state_index must be an integer")
    state_index = int(state_index)
    if state_index < 0 or any(
        not isinstance(result, SimulationResult) or state_index >= result.config.eigenstate_count
        for result in result_sequence
    ):
        raise ValueError("state_index must identify a state present in every result")

    baseline = result_sequence[0].config
    _infinite_well_width(baseline)
    for result in result_sequence[1:]:
        config = result.config
        _infinite_well_width(config)
        if (
            config.experiment,
            config.domain,
            config.parameters,
        ) != (
            baseline.experiment,
            baseline.domain,
            baseline.parameters,
        ):
            raise ValueError("convergence results must share the same physical configuration")

    grid_spacings = np.array(
        [result.x[1] - result.x[0] for result in result_sequence],
        dtype=np.float64,
    )
    if not np.all(np.diff(grid_spacings) < 0.0):
        raise ValueError("convergence results must be ordered coarse-to-fine")

    analytic_energy = infinite_well_analytic_energies(baseline)[state_index]
    relative_energy_errors = np.array(
        [
            abs(result.energies[state_index] - analytic_energy) / analytic_energy
            for result in result_sequence
        ],
        dtype=np.float64,
    )
    if np.any(relative_energy_errors <= 0.0):
        raise ValueError("convergence order requires nonzero energy errors")
    observed_orders = np.log(relative_energy_errors[:-1] / relative_energy_errors[1:]) / np.log(
        grid_spacings[:-1] / grid_spacings[1:]
    )
    return ConvergenceReport(
        grid_spacings=grid_spacings,
        relative_energy_errors=relative_energy_errors,
        observed_orders=observed_orders,
    )


__all__ = [
    "MAX_NORMALIZATION_ERROR",
    "MAX_ORTHOGONALITY_ERROR",
    "MAX_RELATIVE_ENERGY_ERROR",
    "MAX_RELATIVE_RESIDUAL",
    "SECOND_ORDER_TARGET",
    "SECOND_ORDER_TOLERANCE",
    "ConvergenceReport",
    "ValidationReport",
    "assess_infinite_well_convergence",
    "infinite_well_analytic_energies",
    "validate_infinite_well",
]
