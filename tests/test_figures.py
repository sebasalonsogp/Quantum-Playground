from typing import Any

import numpy as np
import plotly.graph_objects as go
import pytest

from quantum_playground.figures import StateQuantity, build_stationary_state_figure
from quantum_playground.potentials import (
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


def test_selected_state_has_text_and_line_style_not_just_color(well_result) -> None:
    figure = build_stationary_state_figure(well_result, state_index=2)
    energy_traces = figure.data[1 : 1 + well_result.config.eigenstate_count]

    assert energy_traces[2].name == "Selected E3"
    assert energy_traces[2].line.dash == "solid"
    assert energy_traces[2].line.width > energy_traces[0].line.width
    assert energy_traces[0].line.dash == "dash"
    assert "state n = 3" in figure.layout.title.text
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

    assert "display-scaled" in overlay.name
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
