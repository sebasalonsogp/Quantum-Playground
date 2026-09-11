from typing import Any

import numpy as np
import pytest

from quantum_playground.models import ExperimentId, SimulationConfig
from quantum_playground.potentials import (
    BARRIER_HEIGHT,
    DOUBLE_WELL_PRESET,
    HARMONIC_OSCILLATOR_PRESET,
    INFINITE_WELL_PRESET,
    OMEGA,
    WELL_SEPARATION,
    create_double_well_config,
    create_harmonic_oscillator_config,
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


def test_harmonic_oscillator_preset_has_one_bounded_frequency_control() -> None:
    preset = HARMONIC_OSCILLATOR_PRESET

    assert preset.experiment is ExperimentId.HARMONIC_OSCILLATOR
    assert preset.title == "Harmonic oscillator"
    assert preset.parameters == (OMEGA,)
    assert OMEGA.key == "omega"
    assert OMEGA.minimum < OMEGA.default < OMEGA.maximum
    assert "frequency" in OMEGA.help_text.lower()
    assert preset.default_grid_points == 1_201
    assert preset.default_eigenstate_count == 6


def test_default_harmonic_config_is_deterministic_on_a_finite_symmetric_domain() -> None:
    config = create_harmonic_oscillator_config()

    assert config == SimulationConfig(
        experiment=ExperimentId.HARMONIC_OSCILLATOR,
        grid_points=1_201,
        domain=(-8.0, 8.0),
        eigenstate_count=6,
        parameters=(("omega", 1.0),),
    )


def test_harmonic_potential_matches_half_omega_squared_x_squared() -> None:
    config = create_harmonic_oscillator_config(omega=1.5, grid_points=401)
    x = np.linspace(*config.domain, config.grid_points)

    potential = evaluate_potential(config, x)

    np.testing.assert_allclose(potential, 0.5 * 1.5**2 * x**2)
    assert potential[config.grid_points // 2] == pytest.approx(0.0)
    assert potential[0] == pytest.approx(potential[-1])
    assert not potential.flags.writeable


@pytest.mark.parametrize("omega", [0.49, 2.01, np.nan, np.inf, True])
def test_harmonic_config_rejects_invalid_frequency(omega: Any) -> None:
    with pytest.raises(ValueError, match="omega"):
        create_harmonic_oscillator_config(omega=omega)


def test_harmonic_potential_rejects_inconsistent_domain_or_parameters() -> None:
    x = np.linspace(-5.0, 5.0, 201)
    for parameters in ((), (("frequency", 1.0),), (("omega", 1.0), ("width", 1.0))):
        config = SimulationConfig(
            experiment=ExperimentId.HARMONIC_OSCILLATOR,
            grid_points=201,
            domain=(-5.0, 5.0),
            eigenstate_count=4,
            parameters=parameters,
        )
        with pytest.raises(ValueError, match="parameters|domain"):
            evaluate_potential(config, x)


def test_double_well_preset_has_two_bounded_geometric_controls() -> None:
    preset = DOUBLE_WELL_PRESET

    assert preset.experiment is ExperimentId.DOUBLE_WELL
    assert preset.title == "Symmetric double well"
    assert preset.parameters == (BARRIER_HEIGHT, WELL_SEPARATION)
    assert BARRIER_HEIGHT.key == "barrier_height"
    assert WELL_SEPARATION.key == "well_separation"
    assert "central barrier" in BARRIER_HEIGHT.help_text.lower()
    assert "minima" in WELL_SEPARATION.help_text.lower()
    assert preset.default_grid_points == 1_201
    assert preset.default_eigenstate_count == 6


def test_default_double_well_config_is_deterministic_on_a_symmetric_domain() -> None:
    config = create_double_well_config()

    assert config == SimulationConfig(
        experiment=ExperimentId.DOUBLE_WELL,
        grid_points=1_201,
        domain=(-6.0, 6.0),
        eigenstate_count=6,
        parameters=(("barrier_height", 4.0), ("well_separation", 3.0)),
    )


def test_double_well_potential_has_symmetric_minima_and_requested_barrier() -> None:
    config = create_double_well_config(
        barrier_height=4.0,
        well_separation=3.0,
    )
    x = np.linspace(*config.domain, config.grid_points)

    potential = evaluate_potential(config, x)

    np.testing.assert_allclose(potential, 4.0 * ((2.0 * x / 3.0) ** 2 - 1.0) ** 2)
    np.testing.assert_allclose(potential, potential[::-1], rtol=0.0, atol=1e-12)
    assert potential[config.grid_points // 2] == pytest.approx(4.0)
    assert potential[np.searchsorted(x, -1.5)] == pytest.approx(0.0, abs=1e-12)
    assert potential[np.searchsorted(x, 1.5)] == pytest.approx(0.0, abs=1e-12)
    assert np.all(potential >= 0.0)
    assert not potential.flags.writeable


def test_double_well_controls_change_only_the_intended_geometric_feature() -> None:
    x = np.linspace(-6.0, 6.0, 1_201)
    lower_barrier = evaluate_potential(
        create_double_well_config(barrier_height=2.5, well_separation=3.0),
        x,
    )
    higher_barrier = evaluate_potential(
        create_double_well_config(barrier_height=6.0, well_separation=3.0),
        x,
    )
    closer_wells = evaluate_potential(
        create_double_well_config(barrier_height=4.0, well_separation=2.0),
        x,
    )
    farther_wells = evaluate_potential(
        create_double_well_config(barrier_height=4.0, well_separation=4.0),
        x,
    )

    center = x.size // 2
    assert lower_barrier[center] == pytest.approx(2.5)
    assert higher_barrier[center] == pytest.approx(6.0)
    for potential in (lower_barrier, higher_barrier):
        assert potential[np.searchsorted(x, -1.5)] == pytest.approx(0.0, abs=1e-12)
        assert potential[np.searchsorted(x, 1.5)] == pytest.approx(0.0, abs=1e-12)
    assert closer_wells[center] == pytest.approx(4.0)
    assert farther_wells[center] == pytest.approx(4.0)
    assert closer_wells[np.searchsorted(x, 1.0)] == pytest.approx(0.0, abs=1e-12)
    assert farther_wells[np.searchsorted(x, 2.0)] == pytest.approx(0.0, abs=1e-12)


@pytest.mark.parametrize(
    ("parameter", "value"),
    [
        ("barrier_height", 2.49),
        ("barrier_height", 8.01),
        ("well_separation", 1.99),
        ("well_separation", 4.01),
        ("well_separation", np.nan),
        ("well_separation", True),
    ],
)
def test_double_well_config_rejects_invalid_parameters(parameter: str, value: Any) -> None:
    controls = {"barrier_height": 4.0, "well_separation": 3.0, parameter: value}

    with pytest.raises(ValueError, match=parameter):
        create_double_well_config(**controls)


def test_double_well_potential_rejects_inconsistent_domain_or_parameters() -> None:
    x = np.linspace(-5.0, 5.0, 201)
    for parameters in (
        (),
        (("barrier_height", 4.0),),
        (("barrier_height", 4.0), ("separation", 3.0)),
        (("barrier_height", 4.0), ("well_separation", 3.0)),
    ):
        config = SimulationConfig(
            experiment=ExperimentId.DOUBLE_WELL,
            grid_points=201,
            domain=(-5.0, 5.0),
            eigenstate_count=4,
            parameters=parameters,
        )
        with pytest.raises(ValueError, match="parameters|domain"):
            evaluate_potential(config, x)
