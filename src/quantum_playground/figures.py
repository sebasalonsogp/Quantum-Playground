"""Pure Plotly figure builders for stationary-state results."""

from enum import StrEnum
from numbers import Integral

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from quantum_playground.models import ExperimentId, FloatArray, SimulationResult

_BACKGROUND = "#07111F"
_TEXT = "#E2E8F0"
_MUTED = "#94A3B8"
_GRID = "rgba(148, 163, 184, 0.14)"
_POTENTIAL = "#22D3EE"
_SELECTED_ENERGY = "#FBBF24"
_OTHER_ENERGY = "rgba(148, 163, 184, 0.62)"
_WAVEFUNCTION = "#A78BFA"
_DENSITY = "#F472B6"
_REFERENCE = "rgba(148, 163, 184, 0.58)"
_REFERENCE_POTENTIAL = "rgba(34, 211, 238, 0.42)"


class StateQuantity(StrEnum):
    """State quantity displayed in the coordinated figure."""

    WAVEFUNCTION = "wavefunction"
    PROBABILITY_DENSITY = "probability_density"


def _validate_selection(
    result: SimulationResult,
    state_index: object,
    quantity: object,
) -> tuple[int, StateQuantity]:
    if not isinstance(result, SimulationResult):
        raise ValueError("result must be a SimulationResult")
    if isinstance(state_index, bool) or not isinstance(state_index, Integral):
        raise ValueError("state_index must be an integer")
    selected_index = int(state_index)
    if not 0 <= selected_index < result.config.eigenstate_count:
        raise ValueError("state_index must identify a computed state")
    if not isinstance(quantity, StateQuantity):
        raise ValueError("quantity must be a StateQuantity")
    return selected_index, quantity


def _profile_values(
    result: SimulationResult,
    state_index: int,
    quantity: StateQuantity,
) -> tuple[FloatArray, str, str, str, str | None]:
    wavefunction = result.wavefunctions[state_index]
    state_number = state_index + 1
    if quantity is StateQuantity.WAVEFUNCTION:
        return (
            wavefunction,
            f"ψ{state_number}(x)",
            "Wavefunction ψ(x)",
            _WAVEFUNCTION,
            None,
        )
    return (
        wavefunction**2,
        f"|ψ{state_number}(x)|²",
        "Probability density |ψ(x)|²",
        _DENSITY,
        "tozeroy",
    )


def _energy_scaled_profile(
    result: SimulationResult,
    state_index: int,
    profile: FloatArray,
) -> FloatArray:
    selected_energy = result.energies[state_index]
    other_energies = np.delete(result.energies, state_index)
    if other_energies.size:
        reference_gap = float(np.min(np.abs(other_energies - selected_energy)))
    else:
        reference_gap = max(abs(float(selected_energy)), 1.0)
    maximum_profile = float(np.max(np.abs(profile)))
    scale = 0.22 * reference_gap / maximum_profile
    return selected_energy + profile * scale


def _validate_comparison_result(
    result: SimulationResult,
    comparison_result: SimulationResult | None,
) -> SimulationResult | None:
    if comparison_result is None:
        return None
    if not isinstance(comparison_result, SimulationResult):
        raise ValueError("comparison_result must be a SimulationResult")
    if (
        result.config.experiment is not ExperimentId.DOUBLE_WELL
        or comparison_result.config.experiment is not ExperimentId.DOUBLE_WELL
    ):
        raise ValueError("reference comparison requires double-well results")
    if result.config.eigenstate_count < 2 or comparison_result.config.eigenstate_count < 2:
        raise ValueError("reference comparison requires at least two states in each result")
    if not np.allclose(
        result.config.domain,
        comparison_result.config.domain,
        rtol=1e-12,
        atol=1e-12,
    ):
        raise ValueError("reference comparison requires matching domains")
    return comparison_result


def _add_reference_context(figure: go.Figure, reference: SimulationResult) -> None:
    figure.add_trace(
        go.Scatter(
            x=reference.x,
            y=reference.potential,
            mode="lines",
            name="Reference V(x)",
            line={"color": _REFERENCE_POTENTIAL, "dash": "dash", "width": 1.8},
            hovertemplate="x = %{x:.4g}<br>Reference V(x) = %{y:.6g}<extra></extra>",
        ),
        row=1,
        col=1,
    )
    lower, upper = reference.config.domain
    for state_index in (0, 1):
        state_number = state_index + 1
        energy = float(reference.energies[state_index])
        figure.add_trace(
            go.Scatter(
                x=(lower, upper),
                y=(energy, energy),
                mode="lines",
                name="Reference E1/E2" if state_index == 0 else "Reference E2",
                legendgroup="reference-lowest-pair",
                showlegend=state_index == 0,
                line={"color": _REFERENCE, "dash": "dot", "width": 1.6},
                hovertemplate=(
                    f"Reference E{state_number} = %{{y:.6g}}<extra>Default baseline</extra>"
                ),
            ),
            row=1,
            col=1,
        )


def _add_energy_levels(
    figure: go.Figure,
    result: SimulationResult,
    state_index: int,
) -> None:
    lower, upper = result.config.domain
    unselected_legend_added = False
    for index, energy in enumerate(result.energies):
        state_number = index + 1
        is_selected = index == state_index
        if is_selected:
            name = f"Selected E{state_number}"
            showlegend = True
        elif not unselected_legend_added:
            name = "Other levels"
            showlegend = True
            unselected_legend_added = True
        else:
            name = f"E{state_number}"
            showlegend = False

        figure.add_trace(
            go.Scatter(
                x=(lower, upper),
                y=(energy, energy),
                mode="lines",
                name=name,
                showlegend=showlegend,
                line={
                    "color": _SELECTED_ENERGY if is_selected else _OTHER_ENERGY,
                    "dash": "solid" if is_selected else "dash",
                    "width": 3.0 if is_selected else 1.4,
                },
                hovertemplate=(f"E{state_number} = %{{y:.6g}}<extra>Energy level</extra>"),
            ),
            row=1,
            col=1,
        )
        figure.add_annotation(
            x=upper,
            y=float(energy),
            text=f"E{state_number}",
            showarrow=False,
            xanchor="left",
            xshift=7,
            font={
                "color": _SELECTED_ENERGY if is_selected else _MUTED,
                "size": 12,
            },
            row=1,
            col=1,
        )


def _add_domain_boundaries(figure: go.Figure, result: SimulationResult) -> None:
    for boundary in result.config.domain:
        for row in (1, 2):
            figure.add_vline(
                x=boundary,
                line={"color": _MUTED, "dash": "dot", "width": 1.2},
                layer="below",
                row=row,
                col=1,
            )


def build_stationary_state_figure(
    result: SimulationResult,
    *,
    state_index: int = 0,
    quantity: StateQuantity = StateQuantity.WAVEFUNCTION,
    comparison_result: SimulationResult | None = None,
) -> go.Figure:
    """Build a coordinated energy landscape and selected-state profile.

    The selected state is scaled only when overlaid on the energy panel. The lower
    panel always displays its true numerical values.

    Source: https://plotly.com/python/subplots/
    """

    state_index, quantity = _validate_selection(result, state_index, quantity)
    comparison_result = _validate_comparison_result(result, comparison_result)
    state_number = state_index + 1
    selected_energy = float(result.energies[state_index])
    profile, profile_name, axis_title, profile_color, fill = _profile_values(
        result,
        state_index,
        quantity,
    )
    scaled_profile = _energy_scaled_profile(result, state_index, profile)

    figure = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        row_heights=(0.68, 0.32),
        vertical_spacing=0.13,
        subplot_titles=(None, f"Displayed state {state_number} · true numerical profile"),
    )
    if comparison_result is not None:
        _add_reference_context(figure, comparison_result)
    figure.add_trace(
        go.Scatter(
            x=result.x,
            y=result.potential,
            mode="lines",
            name="Potential V(x)",
            line={"color": _POTENTIAL, "width": 2.8},
            hovertemplate="x = %{x:.4g}<br>V(x) = %{y:.6g}<extra>Potential</extra>",
        ),
        row=1,
        col=1,
    )
    _add_energy_levels(figure, result, state_index)
    figure.add_trace(
        go.Scatter(
            x=result.x,
            y=scaled_profile,
            customdata=profile,
            mode="lines",
            name=f"{profile_name}, scaled",
            line={"color": profile_color, "width": 2.6},
            hovertemplate=(
                "x = %{x:.4g}<br>Actual value = %{customdata:.6g}"
                "<br>Energy-panel curve is display-scaled<extra></extra>"
            ),
        ),
        row=1,
        col=1,
    )
    figure.add_trace(
        go.Scatter(
            x=result.x,
            y=profile,
            mode="lines",
            name=profile_name,
            showlegend=False,
            line={"color": profile_color, "width": 2.8},
            fill=fill,
            fillcolor="rgba(244, 114, 182, 0.16)" if fill else None,
            hovertemplate=f"x = %{{x:.4g}}<br>{profile_name} = %{{y:.6g}}<extra></extra>",
        ),
        row=2,
        col=1,
    )

    _add_domain_boundaries(figure, result)
    figure.add_hline(
        y=0.0,
        line={"color": _MUTED, "width": 1.0},
        layer="below",
        row=2,
        col=1,
    )

    energy_bounds = [
        float(np.min(result.potential)),
        float(np.min(result.energies)),
        float(np.min(scaled_profile)),
        float(np.max(result.energies)),
        float(np.max(scaled_profile)),
    ]
    metadata = {
        "state_index": state_index,
        "state_number": state_number,
        "quantity": quantity.value,
        "selected_energy": selected_energy,
    }
    if comparison_result is not None:
        energy_bounds.extend(float(energy) for energy in comparison_result.energies[:2])
        metadata["reference_splitting"] = float(
            comparison_result.energies[1] - comparison_result.energies[0]
        )
    energy_min = min(energy_bounds)
    energy_max = max(energy_bounds)
    energy_span = max(energy_max - energy_min, 1.0)
    energy_padding = 0.08 * energy_span
    profile_max = float(np.max(np.abs(profile)))
    profile_range = (
        (-1.1 * profile_max, 1.1 * profile_max)
        if quantity is StateQuantity.WAVEFUNCTION
        else (0.0, 1.08 * profile_max)
    )

    figure.update_layout(
        autosize=True,
        height=720,
        paper_bgcolor=_BACKGROUND,
        plot_bgcolor=_BACKGROUND,
        font={"color": _TEXT, "family": "Inter, ui-sans-serif, system-ui, sans-serif"},
        title={
            "text": f"Energy landscape · displayed state {state_number}",
            "x": 0.0,
            "xanchor": "left",
            "y": 0.83 if comparison_result is not None else 0.88,
            "yanchor": "top",
        },
        legend={
            "orientation": "h",
            "x": 1.0,
            "xanchor": "right",
            "y": 1.16 if comparison_result is not None else 1.11,
            "yanchor": "bottom",
            "bgcolor": "rgba(0, 0, 0, 0)",
            "font": {"size": 11},
        },
        margin={
            "l": 72,
            "r": 64,
            "t": 146 if comparison_result is not None else 120,
            "b": 56,
        },
        hovermode="closest",
        meta=metadata,
    )
    figure.update_xaxes(
        range=list(result.config.domain),
        showgrid=False,
        zeroline=False,
        showline=True,
        linecolor=_MUTED,
        mirror=False,
        automargin=True,
    )
    figure.update_yaxes(
        showgrid=True,
        gridcolor=_GRID,
        zeroline=False,
        showline=True,
        linecolor=_MUTED,
        automargin=True,
    )
    figure.update_yaxes(
        title_text="Energy E",
        range=(energy_min - energy_padding, energy_max + energy_padding),
        row=1,
        col=1,
    )
    figure.update_xaxes(title_text="Position x", row=2, col=1)
    figure.update_yaxes(title_text=axis_title, range=profile_range, row=2, col=1)
    return figure


__all__ = ["StateQuantity", "build_stationary_state_figure"]
