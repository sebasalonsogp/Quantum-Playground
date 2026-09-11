import numpy as np
import pytest

from quantum_playground.models import ExperimentId, SimulationConfig
from quantum_playground.potentials import (
    create_harmonic_oscillator_config,
    create_infinite_well_config,
)
from quantum_playground.solver import solve
from quantum_playground.validation import (
    MAX_HARMONIC_RELATIVE_ENERGY_ERROR,
    MAX_NORMALIZATION_ERROR,
    MAX_ORTHOGONALITY_ERROR,
    MAX_RELATIVE_ENERGY_ERROR,
    MAX_RELATIVE_RESIDUAL,
    SECOND_ORDER_TOLERANCE,
    assess_infinite_well_convergence,
    harmonic_oscillator_analytic_energies,
    infinite_well_analytic_energies,
    validate_harmonic_oscillator,
    validate_infinite_well,
)


def test_analytic_energies_follow_n_squared_and_inverse_width_squared() -> None:
    unit_width = create_infinite_well_config(grid_points=201, eigenstate_count=3)
    double_width = create_infinite_well_config(
        width=2.0,
        grid_points=201,
        eigenstate_count=3,
    )

    unit_energies = infinite_well_analytic_energies(unit_width)
    double_energies = infinite_well_analytic_energies(double_width)

    np.testing.assert_allclose(unit_energies, np.pi**2 * np.array([1.0, 4.0, 9.0]) / 2.0)
    np.testing.assert_allclose(double_energies, unit_energies / 4.0)
    assert not unit_energies.flags.writeable


def test_default_solution_meets_every_documented_validation_tolerance() -> None:
    result = solve(create_infinite_well_config())

    report = validate_infinite_well(result)

    assert report.maximum_relative_energy_error <= MAX_RELATIVE_ENERGY_ERROR
    assert report.maximum_relative_residual <= MAX_RELATIVE_RESIDUAL
    assert report.maximum_normalization_error <= MAX_NORMALIZATION_ERROR
    assert report.orthogonality_error <= MAX_ORTHOGONALITY_ERROR
    assert report.energy_accurate
    assert report.residuals_accurate
    assert report.normalization_accurate
    assert report.orthogonality_accurate
    assert report.passed
    assert not report.analytic_energies.flags.writeable
    assert not report.relative_energy_errors.flags.writeable


def test_harmonic_analytic_energies_are_evenly_spaced_and_scale_with_frequency() -> None:
    unit_frequency = create_harmonic_oscillator_config(eigenstate_count=4)
    higher_frequency = create_harmonic_oscillator_config(
        omega=1.5,
        eigenstate_count=4,
    )

    unit_energies = harmonic_oscillator_analytic_energies(unit_frequency)
    higher_energies = harmonic_oscillator_analytic_energies(higher_frequency)

    np.testing.assert_allclose(unit_energies, np.array([0.5, 1.5, 2.5, 3.5]))
    np.testing.assert_allclose(np.diff(unit_energies), 1.0)
    np.testing.assert_allclose(higher_energies, 1.5 * unit_energies)
    assert not unit_energies.flags.writeable


@pytest.mark.parametrize("omega", [0.5, 1.0, 2.0])
def test_harmonic_solution_meets_stated_finite_domain_tolerance(omega: float) -> None:
    result = solve(create_harmonic_oscillator_config(omega=omega))

    report = validate_harmonic_oscillator(result)

    assert report.relative_energy_tolerance == MAX_HARMONIC_RELATIVE_ENERGY_ERROR
    assert report.maximum_relative_energy_error <= MAX_HARMONIC_RELATIVE_ENERGY_ERROR
    assert report.maximum_relative_residual <= MAX_RELATIVE_RESIDUAL
    assert report.maximum_normalization_error <= MAX_NORMALIZATION_ERROR
    assert report.orthogonality_error <= MAX_ORTHOGONALITY_ERROR
    assert report.passed


def test_validation_report_does_not_hide_under_resolved_energy_error() -> None:
    config = SimulationConfig(
        experiment=ExperimentId.INFINITE_WELL,
        grid_points=21,
        domain=(-0.5, 0.5),
        eigenstate_count=3,
        parameters=(("width", 1.0),),
    )

    report = validate_infinite_well(solve(config))

    assert report.maximum_relative_energy_error > MAX_RELATIVE_ENERGY_ERROR
    assert not report.energy_accurate
    assert not report.passed


def test_grid_refinement_exhibits_second_order_energy_convergence() -> None:
    results = tuple(
        solve(create_infinite_well_config(grid_points=points, eigenstate_count=1))
        for points in (201, 401, 801)
    )

    report = assess_infinite_well_convergence(results)

    assert np.all(np.diff(report.grid_spacings) < 0.0)
    assert np.all(np.diff(report.relative_energy_errors) < 0.0)
    np.testing.assert_allclose(
        report.observed_orders,
        2.0,
        rtol=0.0,
        atol=SECOND_ORDER_TOLERANCE,
    )
    assert report.errors_decrease
    assert report.is_second_order
    assert report.passed


def test_convergence_requires_three_matching_coarse_to_fine_results() -> None:
    coarse = solve(create_infinite_well_config(grid_points=201, eigenstate_count=1))
    medium = solve(create_infinite_well_config(grid_points=401, eigenstate_count=1))
    fine = solve(create_infinite_well_config(grid_points=801, eigenstate_count=1))

    with pytest.raises(ValueError, match="at least three"):
        assess_infinite_well_convergence((coarse, medium))

    with pytest.raises(ValueError, match="coarse-to-fine"):
        assess_infinite_well_convergence((fine, medium, coarse))

    different_width = solve(
        create_infinite_well_config(width=1.2, grid_points=801, eigenstate_count=1)
    )
    with pytest.raises(ValueError, match="same physical configuration"):
        assess_infinite_well_convergence((coarse, medium, different_width))


def test_validation_rejects_non_well_configuration_and_invalid_state_index() -> None:
    oscillator = SimulationConfig(
        experiment=ExperimentId.HARMONIC_OSCILLATOR,
        grid_points=201,
        domain=(-5.0, 5.0),
        eigenstate_count=3,
        parameters=(("omega", 1.0),),
    )

    with pytest.raises(ValueError, match="infinite-well"):
        infinite_well_analytic_energies(oscillator)

    well = create_infinite_well_config(grid_points=201, eigenstate_count=3)
    with pytest.raises(ValueError, match="harmonic-oscillator"):
        harmonic_oscillator_analytic_energies(well)

    results = tuple(
        solve(create_infinite_well_config(grid_points=points, eigenstate_count=1))
        for points in (201, 401, 801)
    )
    with pytest.raises(ValueError, match="state_index"):
        assess_infinite_well_convergence(results, state_index=1)
