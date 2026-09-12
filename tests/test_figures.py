from typing import Any

import numpy as np
import plotly.graph_objects as go
import pytest

from quantum_playground.figures import (
    StateQuantity,
    build_stationary_state_figure,
    build_tunneling_motion_figure,
)
from quantum_playground.potentials import (
    create_double_well_config,
    create_harmonic_oscillator_config,
    create_infinite_well_config,
)
from quantum_playground.solver import solve


@pytest.fixture(scope="module")
def well_result():
    return solve(create_infinite_well_config(grid_points=201, eigenstate_count=4))


def test_figure_coordinates_potential_levels_and_state_across_two_panels(well_result) -> None:
    figure = build_stationary_state_figure(well_result)

    assert isinstance(figure, go.Figure)
    assert len(figure.data) == well_result.config.eigenstate_count + 3
    assert figure.data[0].name == "Potential V(x)"
    np.testing.assert_array_equal(figure.data[0].x, well_result.x)
    np.testing.assert_array_equal(figure.data[0].y, well_result.potential)

    energy_traces = figure.data[1 : 1 + well_result.config.eigenstate_count]
    for index, trace in enumerate(energy_traces):
        assert trace.yaxis == "y"
        np.testing.assert_allclose(trace.y, well_result.energies[index])

    assert figure.data[-2].yaxis == "y"
    assert figure.data[-1].yaxis == "y2"
    assert figure.layout.yaxis.title.text == "Energy E"
    assert figure.layout.xaxis2.title.text == "Position x"
    assert figure.layout.xaxis.zeroline is False
    assert figure.layout.xaxis2.zeroline is False


def test_figure_uses_responsive_margins_and_readable_axis_labels(well_result) -> None:
    figure = build_stationary_state_figure(well_result)

    assert figure.layout.autosize is True
    assert figure.layout.xaxis.automargin is True
    assert figure.layout.xaxis2.automargin is True
    assert figure.layout.yaxis.automargin is True
    assert figure.layout.yaxis2.automargin is True
    assert figure.layout.xaxis2.title.text == "Position x"
    assert figure.layout.yaxis.title.text == "Energy E"
    assert figure.layout.yaxis2.title.text == "Wavefunction ψ(x)"


def test_selected_state_has_text_and_line_style_not_just_color(well_result) -> None:
    figure = build_stationary_state_figure(well_result, state_index=2)
    energy_traces = figure.data[1 : 1 + well_result.config.eigenstate_count]

    assert energy_traces[2].name == "Selected E3"
    assert energy_traces[2].line.dash == "solid"
    assert energy_traces[2].line.width > energy_traces[0].line.width
    assert energy_traces[0].line.dash == "dash"
    assert "displayed state 3" in figure.layout.title.text.lower()
    assert any(annotation.text == "E3" for annotation in figure.layout.annotations)


def test_quantity_switch_uses_true_wavefunction_or_probability_density(well_result) -> None:
    wavefunction_figure = build_stationary_state_figure(
        well_result,
        state_index=1,
        quantity=StateQuantity.WAVEFUNCTION,
    )
    density_figure = build_stationary_state_figure(
        well_result,
        state_index=1,
        quantity=StateQuantity.PROBABILITY_DENSITY,
    )

    np.testing.assert_allclose(wavefunction_figure.data[-1].y, well_result.wavefunctions[1])
    np.testing.assert_allclose(density_figure.data[-1].y, well_result.wavefunctions[1] ** 2)
    assert wavefunction_figure.data[-1].name == "ψ2(x)"
    assert density_figure.data[-1].name == "|ψ2(x)|²"
    assert wavefunction_figure.layout.yaxis2.title.text == "Wavefunction ψ(x)"
    assert density_figure.layout.yaxis2.title.text == "Probability density |ψ(x)|²"
    assert density_figure.data[-1].fill == "tozeroy"


def test_energy_panel_marks_display_scaling_and_preserves_selected_energy(well_result) -> None:
    state_index = 3
    figure = build_stationary_state_figure(well_result, state_index=state_index)
    overlay = figure.data[-2]
    selected_energy = well_result.energies[state_index]

    assert "scaled" in overlay.name
    assert np.min(overlay.y) < selected_energy < np.max(overlay.y)
    assert "display-scaled" in overlay.hovertemplate
    assert figure.layout.meta["selected_energy"] == pytest.approx(selected_energy)


def test_figure_includes_both_domain_boundaries(well_result) -> None:
    figure = build_stationary_state_figure(well_result)

    boundary_positions = {
        float(shape.x0)
        for shape in figure.layout.shapes
        if shape.type == "line" and shape.x0 == shape.x1
    }
    assert boundary_positions == set(well_result.config.domain)


def test_harmonic_figure_keeps_energy_ladder_legible_without_clipping_data() -> None:
    result = solve(create_harmonic_oscillator_config())

    figure = build_stationary_state_figure(result, state_index=5)

    np.testing.assert_array_equal(figure.data[0].y, result.potential)
    assert figure.layout.yaxis.range[1] < float(np.max(result.potential))
    assert figure.layout.yaxis.range[1] > float(np.max(result.energies))
    assert figure.layout.yaxis.range[1] > float(np.max(figure.data[-2].y))


def test_double_well_figure_compares_potential_and_lowest_pair_with_reference() -> None:
    current = solve(
        create_double_well_config(
            barrier_height=8.0,
            well_separation=4.0,
        )
    )
    reference = solve(create_double_well_config())

    figure = build_stationary_state_figure(
        current,
        comparison_result=reference,
    )

    reference_potential = next(trace for trace in figure.data if trace.name == "Reference V(x)")
    reference_levels = [
        trace for trace in figure.data if trace.legendgroup == "reference-lowest-pair"
    ]
    np.testing.assert_array_equal(reference_potential.x, reference.x)
    np.testing.assert_array_equal(reference_potential.y, reference.potential)
    assert reference_potential.line.dash == "dash"
    assert len(reference_levels) == 2
    np.testing.assert_allclose(reference_levels[0].y, reference.energies[0])
    np.testing.assert_allclose(reference_levels[1].y, reference.energies[1])
    assert figure.layout.meta["reference_splitting"] == pytest.approx(
        reference.energies[1] - reference.energies[0]
    )


def test_tunneling_motion_scrubs_a_normalized_density_between_wells() -> None:
    result = solve(create_double_well_config())

    initial_figure = build_tunneling_motion_figure(result, cycle_position=0.0)
    quarter_period_figure = build_tunneling_motion_figure(result, cycle_position=0.25)
    half_period_figure = build_tunneling_motion_figure(result, cycle_position=0.5)
    final_figure = build_tunneling_motion_figure(result, cycle_position=1.0)

    assert isinstance(initial_figure, go.Figure)
    assert not initial_figure.frames
    assert not initial_figure.layout.updatemenus
    assert not initial_figure.layout.sliders
    assert initial_figure.data[0].name == "Localized probability density"
    assert initial_figure.data[0].fill == "tozeroy"
    assert initial_figure.layout.meta["energy_splitting"] == pytest.approx(
        result.energies[1] - result.energies[0]
    )
    assert initial_figure.layout.meta["tunneling_period"] == pytest.approx(
        2.0 * np.pi / (result.energies[1] - result.energies[0])
    )
    assert initial_figure.layout.meta["cycle_position"] == pytest.approx(0.0)
    assert half_period_figure.layout.meta["cycle_position"] == pytest.approx(0.5)

    initial_density = np.asarray(initial_figure.data[0].y)
    quarter_period_density = np.asarray(quarter_period_figure.data[0].y)
    half_period_density = np.asarray(half_period_figure.data[0].y)
    final_density = np.asarray(final_figure.data[0].y)
    for density in (
        initial_density,
        quarter_period_density,
        half_period_density,
        final_density,
    ):
        assert np.trapezoid(density, result.x) == pytest.approx(1.0, abs=2e-6)
        assert np.all(density >= 0.0)
    np.testing.assert_allclose(final_density, initial_density, atol=1e-12)

    left = result.x <= 0.0
    right = result.x >= 0.0
    initial_left = np.trapezoid(initial_density[left], result.x[left])
    initial_right = np.trapezoid(initial_density[right], result.x[right])
    half_left = np.trapezoid(half_period_density[left], result.x[left])
    half_right = np.trapezoid(half_period_density[right], result.x[right])
    quarter_left = np.trapezoid(quarter_period_density[left], result.x[left])
    quarter_right = np.trapezoid(quarter_period_density[right], result.x[right])
    assert abs(initial_left - initial_right) > 0.8
    assert quarter_left == pytest.approx(0.5, abs=2e-3)
    assert quarter_right == pytest.approx(0.5, abs=2e-3)
    assert initial_left == pytest.approx(half_right, abs=2e-3)
    assert initial_right == pytest.approx(half_left, abs=2e-3)
    assert initial_figure.layout.meta["left_probability"] == pytest.approx(initial_left)
    assert initial_figure.layout.meta["right_probability"] == pytest.approx(initial_right)


def test_tunneling_motion_requires_two_double_well_states() -> None:
    harmonic = solve(create_harmonic_oscillator_config())
    double_well = solve(create_double_well_config())
    one_state_double_well = solve(create_double_well_config(eigenstate_count=1))

    with pytest.raises(ValueError, match="double-well"):
        build_tunneling_motion_figure(harmonic)

    with pytest.raises(ValueError, match="at least two"):
        build_tunneling_motion_figure(one_state_double_well)

    for invalid_position in (-0.1, 1.1, float("nan"), True):
        with pytest.raises(ValueError, match="cycle_position"):
            build_tunneling_motion_figure(double_well, cycle_position=invalid_position)


def test_reference_comparison_requires_two_compatible_double_well_states() -> None:
    double_well = solve(create_double_well_config())
    harmonic = solve(create_harmonic_oscillator_config())
    one_state_double_well = solve(create_double_well_config(eigenstate_count=1))

    with pytest.raises(ValueError, match="double-well"):
        build_stationary_state_figure(double_well, comparison_result=harmonic)

    with pytest.raises(ValueError, match="at least two"):
        build_stationary_state_figure(double_well, comparison_result=one_state_double_well)

    with pytest.raises(ValueError, match="at least two"):
        build_stationary_state_figure(one_state_double_well, comparison_result=double_well)


def test_figure_structure_is_deterministic(well_result) -> None:
    first = build_stationary_state_figure(well_result, state_index=2)
    second = build_stationary_state_figure(well_result, state_index=2)

    assert first.to_json() == second.to_json()


@pytest.mark.parametrize("state_index", [-1, 4, 1.5, True])
def test_figure_rejects_invalid_state_selection(well_result, state_index: Any) -> None:
    with pytest.raises(ValueError, match="state_index"):
        build_stationary_state_figure(well_result, state_index=state_index)


def test_figure_requires_typed_quantity(well_result) -> None:
    with pytest.raises(ValueError, match="quantity"):
        build_stationary_state_figure(well_result, quantity="wavefunction")
