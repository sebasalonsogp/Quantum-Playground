from dataclasses import FrozenInstanceError
from typing import Any

import numpy as np
import pytest

from quantum_playground.models import (
    BOUNDARY_CONDITION,
    HBAR,
    PARTICLE_MASS,
    BoundaryCondition,
    ExperimentId,
    NumericalDiagnostics,
    SimulationConfig,
    SimulationResult,
)


def make_config(**changes: object) -> SimulationConfig:
    values: dict[str, Any] = {
        "experiment": ExperimentId.INFINITE_WELL,
        "grid_points": 5,
        "domain": (-1.0, 1.0),
        "eigenstate_count": 2,
        "parameters": (("width", 2.0),),
    }
    values.update(changes)
    return SimulationConfig(**values)


def make_result(**changes: object) -> SimulationResult:
    values: dict[str, Any] = {
        "config": make_config(),
        "x": np.linspace(-1.0, 1.0, 5),
        "potential": np.zeros(5),
        "energies": np.array([1.0, 4.0]),
        "wavefunctions": np.array(
            [
                [0.0, 0.5, 1.0, 0.5, 0.0],
                [0.0, -1.0, 0.0, 1.0, 0.0],
            ]
        ),
        "diagnostics": NumericalDiagnostics(
            residual_norms=np.array([1e-12, 2e-12]),
            normalization_errors=np.array([0.0, 1e-15]),
            orthogonality_error=2e-15,
        ),
        "solve_time_seconds": 0.01,
    }
    values.update(changes)
    return SimulationResult(**values)


def test_dimensionless_dirichlet_convention_is_explicit() -> None:
    assert HBAR == 1.0
    assert PARTICLE_MASS == 1.0
    assert BOUNDARY_CONDITION is BoundaryCondition.DIRICHLET


def test_experiment_identifiers_are_stable_strings() -> None:
    assert [experiment.value for experiment in ExperimentId] == [
        "infinite_well",
        "harmonic_oscillator",
        "double_well",
    ]


def test_config_is_immutable_hashable_and_canonicalizes_parameters() -> None:
    config = make_config(parameters=(("width", 2), ("barrier", 1.5)))

    assert config.domain == (-1.0, 1.0)
    assert config.parameters == (("barrier", 1.5), ("width", 2.0))
    assert config.interior_point_count == 3
    assert isinstance(hash(config), int)
    with pytest.raises(FrozenInstanceError):
        config.__setattr__("grid_points", 9)


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"experiment": "infinite_well"}, "experiment"),
        ({"grid_points": 3}, "grid_points"),
        ({"grid_points": True}, "grid_points"),
        ({"domain": (1.0, -1.0)}, "domain"),
        ({"domain": (-np.inf, 1.0)}, "finite"),
        ({"eigenstate_count": 0}, "eigenstate_count"),
        ({"eigenstate_count": 3}, "interior"),
        ({"parameters": (("width", np.nan),)}, "finite"),
        ({"parameters": (("", 2.0),)}, "name"),
        ({"parameters": (("width", 2.0), ("width", 3.0))}, "unique"),
    ],
)
def test_config_rejects_invalid_inputs(changes: dict[str, object], message: str) -> None:
    with pytest.raises(ValueError, match=message):
        make_config(**changes)


def test_result_owns_read_only_float64_arrays() -> None:
    source = np.linspace(-1.0, 1.0, 5, dtype=np.float32)
    result = make_result(x=source)
    source[0] = 99.0

    assert result.x.dtype == np.float64
    assert result.x[0] == -1.0
    assert not result.x.flags.writeable
    assert not result.diagnostics.residual_norms.flags.writeable
    with pytest.raises(ValueError, match="read-only"):
        result.x[0] = 0.0


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"x": np.linspace(-1.0, 1.0, 4)}, "x must have shape"),
        ({"potential": np.zeros(4)}, "potential must have shape"),
        ({"energies": np.array([1.0])}, "energies must have shape"),
        ({"energies": np.array([4.0, 1.0])}, "ascending"),
        ({"wavefunctions": np.zeros((5, 2))}, "wavefunctions must have shape"),
        ({"x": np.array([-1.0, -0.5, 0.25, 0.5, 1.0])}, "uniform"),
        ({"x": np.linspace(-2.0, 1.0, 5)}, "domain endpoints"),
        ({"wavefunctions": np.ones((2, 5))}, "Dirichlet"),
        ({"solve_time_seconds": -0.1}, "solve_time_seconds"),
    ],
)
def test_result_rejects_contract_violations(changes: dict[str, object], message: str) -> None:
    with pytest.raises(ValueError, match=message):
        make_result(**changes)


def test_diagnostics_reject_invalid_values() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        NumericalDiagnostics(
            residual_norms=np.array([-1.0]),
            normalization_errors=np.array([0.0]),
            orthogonality_error=0.0,
        )

    with pytest.raises(ValueError, match="orthogonality_error"):
        NumericalDiagnostics(
            residual_norms=np.array([0.0]),
            normalization_errors=np.array([0.0]),
            orthogonality_error=np.inf,
        )
