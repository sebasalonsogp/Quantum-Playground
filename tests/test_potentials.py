from typing import Any

import numpy as np
import pytest

from quantum_playground.models import ExperimentId, SimulationConfig
from quantum_playground.potentials import (
    INFINITE_WELL_PRESET,
    create_infinite_well_config,
    evaluate_potential,
)


def test_infinite_well_preset_has_bounded_recruiter_facing_metadata() -> None:
    preset = INFINITE_WELL_PRESET
    width = preset.parameters[0]

    assert preset.experiment is ExperimentId.INFINITE_WELL
    assert preset.title == "Infinite square well"
    assert "converg" in preset.description.lower()
    assert "exact" in preset.insight.lower()
    assert width.key == "width"
    assert width.minimum < width.default < width.maximum
    assert width.step > 0
    assert preset.minimum_grid_points <= preset.default_grid_points <= preset.maximum_grid_points
    assert 500 <= preset.default_grid_points - 2 <= 1_000
    assert preset.default_eigenstate_count == 6


def test_default_config_is_deterministic_and_uses_symmetric_dirichlet_domain() -> None:
    config = create_infinite_well_config()

    assert config == SimulationConfig(
        experiment=ExperimentId.INFINITE_WELL,
        grid_points=801,
        domain=(-0.5, 0.5),
        eigenstate_count=6,
        parameters=(("width", 1.0),),
    )


def test_custom_width_sets_domain_and_canonical_parameter() -> None:
    config = create_infinite_well_config(width=1.6, grid_points=1_001, eigenstate_count=4)

    assert config.domain == pytest.approx((-0.8, 0.8))
    assert config.parameters == (("width", 1.6),)
    assert config.grid_points == 1_001
    assert config.eigenstate_count == 4


@pytest.mark.parametrize("width", [0.49, 2.01, np.nan, np.inf, True])
def test_config_factory_rejects_invalid_width(width: Any) -> None:
    with pytest.raises(ValueError, match="width"):
        create_infinite_well_config(width=width)


@pytest.mark.parametrize("grid_points", [200, 1_202, 800, True])
def test_config_factory_rejects_invalid_grid_resolution(grid_points: Any) -> None:
    with pytest.raises(ValueError, match="grid_points"):
        create_infinite_well_config(grid_points=grid_points)


def test_evaluate_potential_returns_finite_zero_interior_values() -> None:
    config = create_infinite_well_config(grid_points=201)
    x = np.linspace(*config.domain, config.grid_points, dtype=np.float32)

    potential = evaluate_potential(config, x)

    assert potential.shape == x.shape
    assert potential.dtype == np.float64
    assert np.all(np.isfinite(potential[1:-1]))
    assert np.all(potential == 0.0)
    assert not potential.flags.writeable


def test_evaluate_potential_accepts_float32_grid_for_custom_width() -> None:
    config = create_infinite_well_config(width=1.6, grid_points=201)
    x = np.linspace(*config.domain, config.grid_points, dtype=np.float32)

    potential = evaluate_potential(config, x)

    assert potential.shape == (config.grid_points,)


def test_evaluate_potential_rejects_inconsistent_configuration() -> None:
    config = SimulationConfig(
        experiment=ExperimentId.INFINITE_WELL,
        grid_points=201,
        domain=(-1.0, 1.0),
        eigenstate_count=4,
        parameters=(("width", 1.0),),
    )
    x = np.linspace(*config.domain, config.grid_points)

    with pytest.raises(ValueError, match="domain"):
        evaluate_potential(config, x)


def test_evaluate_potential_rejects_unknown_or_missing_parameters() -> None:
    x = np.linspace(-0.5, 0.5, 201)

    for parameters in ((), (("depth", 1.0),), (("width", 1.0), ("depth", 1.0))):
        config = SimulationConfig(
            experiment=ExperimentId.INFINITE_WELL,
            grid_points=201,
            domain=(-0.5, 0.5),
            eigenstate_count=4,
            parameters=parameters,
        )
        with pytest.raises(ValueError, match="parameters"):
            evaluate_potential(config, x)


def test_evaluate_potential_rejects_grid_that_does_not_match_config() -> None:
    config = create_infinite_well_config(grid_points=201)

    with pytest.raises(ValueError, match="shape"):
        evaluate_potential(config, np.linspace(*config.domain, 200))

    with pytest.raises(ValueError, match="domain"):
        evaluate_potential(config, np.linspace(-1.0, 1.0, config.grid_points))


def test_evaluate_potential_rejects_unimplemented_experiment() -> None:
    config = SimulationConfig(
        experiment=ExperimentId.HARMONIC_OSCILLATOR,
        grid_points=201,
        domain=(-5.0, 5.0),
        eigenstate_count=4,
        parameters=(("omega", 1.0),),
    )

    with pytest.raises(ValueError, match="not implemented"):
        evaluate_potential(config, np.linspace(*config.domain, config.grid_points))
