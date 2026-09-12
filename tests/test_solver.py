import numpy as np
import pytest
from scipy.sparse import csr_array
from scipy.sparse.linalg import ArpackError, ArpackNoConvergence

from quantum_playground.models import ExperimentId, SimulationConfig
from quantum_playground.potentials import (
    create_double_well_config,
    create_harmonic_oscillator_config,
    create_infinite_well_config,
)
from quantum_playground.solver import (
    SolverError,
    build_hamiltonian,
    build_spatial_grid,
    solve,
)


def _small_well_config(*, grid_points: int = 21, eigenstate_count: int = 3) -> SimulationConfig:
    return SimulationConfig(
        experiment=ExperimentId.INFINITE_WELL,
        grid_points=grid_points,
        domain=(-0.5, 0.5),
        eigenstate_count=eigenstate_count,
        parameters=(("width", 1.0),),
    )


def test_build_spatial_grid_returns_uniform_read_only_float64_grid() -> None:
    config = _small_well_config(grid_points=5, eigenstate_count=1)

    x = build_spatial_grid(config)

    np.testing.assert_array_equal(x, np.array([-0.5, -0.25, 0.0, 0.25, 0.5]))
    assert x.dtype == np.float64
    assert not x.flags.writeable


def test_build_hamiltonian_uses_sparse_symmetric_dirichlet_stencil() -> None:
    config = _small_well_config(grid_points=5, eigenstate_count=1)
    x = build_spatial_grid(config)
    potential = np.zeros(config.grid_points)

    hamiltonian = build_hamiltonian(config, x, potential)

    assert isinstance(hamiltonian, csr_array)
    assert hamiltonian.shape == (3, 3)
    np.testing.assert_array_equal(
        hamiltonian.toarray(),
        np.array([[16.0, -8.0, 0.0], [-8.0, 16.0, -8.0], [0.0, -8.0, 16.0]]),
    )


def test_build_hamiltonian_adds_only_interior_potential_samples() -> None:
    config = _small_well_config(grid_points=5, eigenstate_count=1)
    x = build_spatial_grid(config)
    potential = np.array([99.0, 1.0, 2.0, 3.0, 99.0])

    hamiltonian = build_hamiltonian(config, x, potential)

    np.testing.assert_array_equal(hamiltonian.diagonal(), np.array([17.0, 18.0, 19.0]))


@pytest.mark.parametrize(
    ("x", "potential", "message"),
    [
        (np.array([-0.5, -0.2, 0.0, 0.25, 0.5]), np.zeros(5), "uniform"),
        (np.linspace(-0.5, 0.5, 5), np.zeros(4), "potential"),
        (np.linspace(-0.5, 0.5, 5), np.array([0.0, 0.0, np.nan, 0.0, 0.0]), "finite"),
    ],
)
def test_build_hamiltonian_rejects_invalid_sampled_inputs(
    x: np.ndarray, potential: np.ndarray, message: str
) -> None:
    config = _small_well_config(grid_points=5, eigenstate_count=1)

    with pytest.raises(ValueError, match=message):
        build_hamiltonian(config, x, potential)


def test_solve_returns_lowest_discrete_eigenpairs_in_contract_order() -> None:
    config = _small_well_config(grid_points=21, eigenstate_count=3)

    result = solve(config)

    dx = 1.0 / (config.grid_points - 1)
    state_numbers = np.arange(1, config.eigenstate_count + 1)
    expected_energies = (1.0 - np.cos(state_numbers * np.pi / (config.grid_points - 1))) / dx**2
    np.testing.assert_allclose(result.energies, expected_energies, rtol=1e-12, atol=1e-12)
    assert result.wavefunctions.shape == (config.eigenstate_count, config.grid_points)
    assert np.all(np.diff(result.energies) > 0.0)
    assert np.all(result.wavefunctions[:, (0, -1)] == 0.0)
    assert result.config == config
    assert result.solve_time_seconds >= 0.0


def test_solve_continuously_normalizes_and_canonicalizes_wavefunctions() -> None:
    result = solve(_small_well_config(grid_points=101, eigenstate_count=4))

    norms = np.trapezoid(result.wavefunctions**2, result.x, axis=1)
    overlap = np.trapezoid(
        result.wavefunctions[:, np.newaxis, :] * result.wavefunctions[np.newaxis, :, :],
        result.x,
        axis=2,
    )

    np.testing.assert_allclose(norms, 1.0, rtol=0.0, atol=1e-12)
    np.testing.assert_allclose(overlap, np.eye(4), rtol=0.0, atol=1e-12)
    for wavefunction in result.wavefunctions:
        assert wavefunction[np.argmax(np.abs(wavefunction))] > 0.0


def test_solve_reports_small_raw_numerical_diagnostics() -> None:
    result = solve(_small_well_config(grid_points=101, eigenstate_count=4))

    assert result.diagnostics.residual_norms.shape == (4,)
    assert np.max(result.diagnostics.residual_norms) < 1e-11
    assert np.max(result.diagnostics.normalization_errors) < 1e-12
    assert result.diagnostics.orthogonality_error < 1e-12


def test_solve_wraps_non_convergence_without_returning_partial_results(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_to_converge(*args: object, **kwargs: object) -> None:
        raise ArpackNoConvergence(
            "ARPACK stopped early",
            np.array([1.0]),
            np.ones((19, 1)),
        )

    monkeypatch.setattr("quantum_playground.solver.eigsh", fail_to_converge)

    with pytest.raises(SolverError, match="did not converge") as error:
        solve(_small_well_config())

    assert isinstance(error.value.__cause__, ArpackNoConvergence)


def test_solve_wraps_other_arpack_failures(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_with_arpack_error(*args: object, **kwargs: object) -> None:
        raise ArpackError("ARPACK internal error")

    monkeypatch.setattr("quantum_playground.solver.eigsh", fail_with_arpack_error)

    with pytest.raises(SolverError, match="eigensolver failed") as error:
        solve(_small_well_config())

    assert isinstance(error.value.__cause__, ArpackError)


def test_default_infinite_well_solve_is_complete_and_finite() -> None:
    config = create_infinite_well_config()

    result = solve(config)

    assert result.x.shape == (801,)
    assert result.energies.shape == (6,)
    assert result.wavefunctions.shape == (6, 801)
    assert np.all(np.isfinite(result.energies))
    assert np.all(np.isfinite(result.wavefunctions))


@pytest.mark.parametrize(
    "config",
    [
        create_infinite_well_config(width=0.5, grid_points=1_201),
        create_infinite_well_config(width=2.0, grid_points=1_201),
        create_harmonic_oscillator_config(omega=0.5, grid_points=1_601),
        create_harmonic_oscillator_config(omega=2.0, grid_points=1_601),
        create_double_well_config(
            barrier_height=2.5,
            well_separation=2.0,
            grid_points=1_601,
        ),
        create_double_well_config(
            barrier_height=8.0,
            well_separation=4.0,
            grid_points=1_601,
        ),
    ],
    ids=(
        "narrow-infinite-well",
        "wide-infinite-well",
        "low-frequency-oscillator",
        "high-frequency-oscillator",
        "low-close-double-well",
        "high-separated-double-well",
    ),
)
def test_extreme_allowed_controls_produce_complete_finite_results(
    config: SimulationConfig,
) -> None:
    result = solve(config)

    assert result.config == config
    assert result.wavefunctions.shape == (config.eigenstate_count, config.grid_points)
    assert np.all(np.isfinite(result.energies))
    assert np.all(np.isfinite(result.wavefunctions))
    assert np.max(result.diagnostics.residual_norms) < 1e-8
    assert np.max(result.diagnostics.normalization_errors) < 1e-12
    assert result.diagnostics.orthogonality_error < 1e-10


def test_default_double_well_has_low_even_odd_tunneling_partners() -> None:
    result = solve(create_double_well_config())

    assert result.energies[0] < result.energies[1] < 4.0
    assert result.energies[1] - result.energies[0] > 0.0
    np.testing.assert_allclose(
        result.wavefunctions[0],
        result.wavefunctions[0, ::-1],
        rtol=0.0,
        atol=1e-9,
    )
    np.testing.assert_allclose(
        result.wavefunctions[1],
        -result.wavefunctions[1, ::-1],
        rtol=0.0,
        atol=1e-9,
    )


@pytest.mark.parametrize(
    ("barrier_height", "well_separation"),
    [(2.5, 2.0), (2.5, 4.0), (8.0, 2.0), (8.0, 4.0)],
)
def test_double_well_low_pair_stays_below_barrier_across_control_bounds(
    barrier_height: float,
    well_separation: float,
) -> None:
    result = solve(
        create_double_well_config(
            barrier_height=barrier_height,
            well_separation=well_separation,
            eigenstate_count=2,
        )
    )

    assert result.energies[1] < barrier_height


def test_double_well_splitting_decreases_with_barrier_height_and_separation() -> None:
    low_barrier = solve(
        create_double_well_config(
            barrier_height=2.5,
            well_separation=3.0,
            eigenstate_count=2,
        )
    )
    high_barrier = solve(
        create_double_well_config(
            barrier_height=8.0,
            well_separation=3.0,
            eigenstate_count=2,
        )
    )
    close_wells = solve(
        create_double_well_config(
            barrier_height=4.0,
            well_separation=2.0,
            eigenstate_count=2,
        )
    )
    far_wells = solve(
        create_double_well_config(
            barrier_height=4.0,
            well_separation=4.0,
            eigenstate_count=2,
        )
    )

    low_barrier_splitting = low_barrier.energies[1] - low_barrier.energies[0]
    high_barrier_splitting = high_barrier.energies[1] - high_barrier.energies[0]
    close_well_splitting = close_wells.energies[1] - close_wells.energies[0]
    far_well_splitting = far_wells.energies[1] - far_wells.energies[0]

    assert 0.0 < high_barrier_splitting < low_barrier_splitting
    assert 0.0 < far_well_splitting < close_well_splitting
