import json
import re
from pathlib import Path

import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

import quantum_playground.solver as solver
import quantum_playground.validation as validation

APP_PATH = Path(__file__).parents[1] / "app.py"
DEFAULT_TIMEOUT = 10


def load_app() -> AppTest:
    return AppTest.from_file(APP_PATH, default_timeout=DEFAULT_TIMEOUT).run()


def diagnostics_table(app: AppTest):
    return next(table.value for table in app.table if "Observed" in table.value.columns)


def math_scientific_to_float(value: str) -> float:
    match = re.fullmatch(r"\$(-?\d+\.\d+) \\times 10\^\{(-?\d+)\}\$", value)
    assert match is not None
    coefficient, exponent = match.groups()
    return float(coefficient) * 10 ** int(exponent)


def test_app_loads_with_project_identity() -> None:
    app = load_app()

    assert not app.exception
    assert app.title[0].value == "Quantum Playground"
    assert app.selectbox(key="experiment").value == "Infinite square well"
    assert app.slider(key="well_width").value == 1.0
    assert app.slider(key="grid_points").value == 801
    assert app.slider(key="state_number").value == 1
    assert app.toggle(key="show_density").value is False
    assert any(element.label == r"Selected energy $E_{1}$" for element in app.metric)
    assert any(
        value.startswith(":green-badge[") and "Numerically verified" in value
        for value in (element.value for element in app.markdown)
    )
    assert any(
        "https://github.com/sebasalonsogp/Quantum-Playground" in element.value
        for element in app.caption
    )


def test_chart_disables_zoom_and_selection_controls() -> None:
    app = load_app()

    chart = app.get("plotly_chart")[0]
    config = json.loads(chart.proto.config)
    removed_buttons = set(config["modeBarButtonsToRemove"])

    assert config["scrollZoom"] is False
    assert config["doubleClick"] is False
    assert {
        "zoom2d",
        "pan2d",
        "select2d",
        "lasso2d",
        "zoomIn2d",
        "zoomOut2d",
        "autoScale2d",
        "resetScale2d",
    } <= removed_buttons


def test_sidebar_state_adapts_to_narrow_viewports(monkeypatch) -> None:
    page_config = {}
    set_page_config = st.set_page_config

    def capture_page_config(**kwargs) -> None:
        page_config.update(kwargs)
        set_page_config(**kwargs)

    monkeypatch.setattr(st, "set_page_config", capture_page_config)

    app = load_app()

    assert not app.exception
    assert page_config["initial_sidebar_state"] == "auto"


def test_accessibility_hierarchy_matches_the_visual_reading_order() -> None:
    app = load_app()

    assert not app.exception
    assert len(app.title) == 1
    assert any(header.value == "Infinite square well" for header in app.header)
    section_headings = [subheader.value for subheader in app.subheader]
    assert section_headings.index("Live result") < section_headings.index(
        "Reading the wavefunction"
    )
    assert any("update automatically" in caption.value for caption in app.caption)
    assert app.toggle(key="show_density").label == "Show probability density"
    assert app.button(key="reset_controls").label == "Reset experiment"


def test_result_metrics_prioritize_decisions_without_diagnostic_overload() -> None:
    app = load_app()

    assert not app.exception
    assert [metric.label for metric in app.metric] == [
        r"Selected energy $E_{1}$",
        "Analytic energy error",
        "Solve time",
    ]
    assert all(metric.proto.show_border for metric in app.metric)


def test_diagnostics_use_a_compact_signal_with_expandable_evidence() -> None:
    app = load_app()

    assert not app.exception
    assert not app.success
    assert any(status.label == "Numerical details" for status in app.status)
    assert any("second-order centered finite difference" in item.value for item in app.markdown)
    assert any(
        "Grid: 801 points" in caption.value and r"\Delta x" in caption.value
        for caption in app.caption
    )

    evidence = diagnostics_table(app)
    assert evidence["Check"].tolist() == [
        "Analytic energy",
        "Eigenpair residual",
        "Wavefunction normalization",
        "State orthogonality",
    ]
    assert evidence["Status"].tolist() == [":green-badge[Pass]"] * 4
    assert evidence["Observed"].str.match(r"\$\d\.\d\d \\times 10\^\{-?\d+\}\$").all()
    assert evidence["Limit"].str.match(r"\$\\le \d\.\d \\times 10\^\{-?\d+\}\$").all()
    spectrum = next(table.value for table in app.table if "Relative error" in table.value.columns)
    assert spectrum["Relative error"].str.match(r"\$\d\.\d\d \\times 10\^\{-?\d+\}\$").all()


def test_diagnostics_offer_on_demand_convergence_evidence() -> None:
    app = load_app()

    app.button(key="run_convergence").click().run()

    assert not app.exception
    assert any(
        value.startswith(":green-badge[") and "Second-order convergence confirmed" in value
        for value in (element.value for element in app.markdown)
    )
    convergence = next(table.value for table in app.table if "Grid points" in table.value.columns)
    assert convergence["Grid points"].tolist() == [201, 401, 801]
    assert convergence["Observed order"].tolist()[0] == "—"
    assert (
        convergence["Relative ground-state error"]
        .str.match(r"\$\d\.\d\d \\times 10\^\{-?\d+\}\$")
        .all()
    )
    assert all(
        float(order) == pytest.approx(2.0, abs=0.01) for order in convergence["Observed order"][1:]
    )


def test_failed_diagnostics_are_visibly_marked_untrustworthy(monkeypatch) -> None:
    original_validate = validation.validate_infinite_well

    def fail_residual_check(result):
        report = original_validate(result)
        return validation.ValidationReport(
            analytic_energies=report.analytic_energies,
            relative_energy_errors=report.relative_energy_errors,
            maximum_relative_residual=10 * validation.MAX_RELATIVE_RESIDUAL,
            maximum_normalization_error=report.maximum_normalization_error,
            orthogonality_error=report.orthogonality_error,
            relative_energy_tolerance=report.relative_energy_tolerance,
        )

    monkeypatch.setattr(validation, "validate_infinite_well", fail_residual_check)
    app = load_app()

    assert not app.exception
    assert any(
        value.startswith(":red-badge[") and "Verification failed" in value
        for value in (element.value for element in app.markdown)
    )
    assert any("Do not treat this result as validated" in error.value for error in app.error)
    evidence = diagnostics_table(app)
    residual = evidence.loc[evidence["Check"] == "Eigenpair residual"].iloc[0]
    assert residual["Status"] == ":red-badge[Fail]"


def test_double_well_diagnostics_expose_numerical_checks_without_an_exact_claim() -> None:
    app = load_app()
    app.selectbox(key="experiment").set_value("Symmetric double well").run()

    assert not app.exception
    evidence = diagnostics_table(app)
    assert evidence["Check"].tolist() == [
        "Eigenpair residual",
        "Wavefunction normalization",
        "State orthogonality",
    ]
    assert evidence["Status"].tolist() == [":green-badge[Pass]"] * 3
    assert any("No elementary exact spectrum" in caption.value for caption in app.caption)


def test_resolution_control_recomputes_the_shared_simulation() -> None:
    app = load_app()
    initial_error = next(
        element.value for element in app.metric if element.label == "Analytic energy error"
    )

    app.slider(key="grid_points").set_value(401).run()

    assert not app.exception
    assert app.session_state["grid_points"] == 401
    assert any("401 grid points" in caption.value for caption in app.caption)
    updated_error = next(
        element.value for element in app.metric if element.label == "Analytic energy error"
    )
    assert math_scientific_to_float(updated_error) > math_scientific_to_float(initial_error)


def test_state_selection_and_density_toggle_update_the_explanation() -> None:
    app = load_app()

    app.slider(key="state_number").set_value(4).run()
    app.toggle(key="show_density").set_value(True).run()

    assert not app.exception
    assert any(element.label == r"Selected energy $E_{4}$" for element in app.metric)
    assert any("3 internal nodes" in element.value for element in app.markdown)
    assert any("probability density" in element.value.lower() for element in app.markdown)


def test_bounded_cache_reuses_stable_config_and_recomputes_physical_changes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cache_data = st.cache_data
    cache_options: list[dict[str, object]] = []
    solve_calls = 0
    real_solve = solver.solve

    def capture_cache_options(*args: object, **kwargs: object):
        cache_options.append(kwargs)
        return cache_data(*args, **kwargs)

    def count_solve_calls(config):
        nonlocal solve_calls
        solve_calls += 1
        return real_solve(config)

    cache_data.clear()
    monkeypatch.setattr(st, "cache_data", capture_cache_options)
    monkeypatch.setattr(solver, "solve", count_solve_calls)

    try:
        app = load_app()
        assert solve_calls == 1

        app.slider(key="state_number").set_value(2).run()
        app.toggle(key="show_density").set_value(True).run()

        assert not app.exception
        assert solve_calls == 1

        app.slider(key="well_width").set_value(1.1).run()

        assert not app.exception
        assert solve_calls == 2
        assert cache_options
        assert {options["max_entries"] for options in cache_options} == {16}
    finally:
        cache_data.clear()


def test_solver_failure_replaces_results_with_actionable_feedback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cache_data = st.cache_data
    cache_data.clear()
    app = load_app()
    assert app.metric
    assert app.get("plotly_chart")

    def fail_to_solve(*args: object, **kwargs: object) -> None:
        raise solver.SolverError("stationary-state solve did not converge")

    monkeypatch.setattr(solver, "solve", fail_to_solve)
    cache_data.clear()

    try:
        app.slider(key="well_width").set_value(1.1).run()

        assert not app.exception
        assert len(app.error) == 1
        assert "Try resetting the experiment" in app.error[0].value
        assert not app.metric
        assert not app.get("plotly_chart")
        assert not app.status
    finally:
        cache_data.clear()


def test_switching_to_harmonic_updates_controls_result_and_explanation() -> None:
    app = load_app()

    app.selectbox(key="experiment").set_value("Harmonic oscillator").run()

    assert not app.exception
    assert app.slider(key="oscillator_omega").value == 1.0
    slider_keys = {slider.key for slider in app.slider}
    assert "well_width" not in slider_keys
    assert "grid_points" not in slider_keys
    assert any(header.value == "Harmonic oscillator" for header in app.header)
    selected_energy = next(
        element.value for element in app.metric if element.label == r"Selected energy $E_{1}$"
    )
    assert float(selected_energy) == pytest.approx(0.5, abs=1e-4)
    assert any("evenly spaced" in element.value for element in app.markdown)
    assert any("1,201 grid points" in caption.value for caption in app.caption)


def test_harmonic_frequency_changes_spacing_and_reset() -> None:
    app = load_app()
    app.selectbox(key="experiment").set_value("Harmonic oscillator").run()
    initial_energy = next(
        element.value for element in app.metric if element.label == r"Selected energy $E_{1}$"
    )

    app.slider(key="oscillator_omega").set_value(2.0).run()

    updated_energy = next(
        element.value for element in app.metric if element.label == r"Selected energy $E_{1}$"
    )
    assert float(updated_energy) == pytest.approx(2.0 * float(initial_energy), abs=1e-4)
    assert any(r"\omega = 2.0" in caption.value for caption in app.caption)

    app.selectbox(key="experiment").set_value("Infinite square well").run()
    assert app.slider(key="well_width").value == 1.0
    app.selectbox(key="experiment").set_value("Harmonic oscillator").run()
    assert app.slider(key="oscillator_omega").value == 2.0

    app.slider(key="state_number").set_value(4).run()
    app.toggle(key="show_density").set_value(True).run()
    app.button(key="reset_controls").click().run()

    assert not app.exception
    assert app.slider(key="oscillator_omega").value == 1.0
    assert app.slider(key="state_number").value == 1
    assert app.toggle(key="show_density").value is False


def test_switching_to_double_well_reveals_flagship_controls_and_splitting() -> None:
    app = load_app()

    app.selectbox(key="experiment").set_value("Symmetric double well").run()

    assert not app.exception
    assert app.slider(key="double_well_barrier_height").value == 4.0
    assert app.slider(key="double_well_separation").value == 3.0
    assert app.toggle(key="show_baseline").value is True
    slider_keys = {slider.key for slider in app.slider}
    assert "well_width" not in slider_keys
    assert "grid_points" not in slider_keys
    assert "oscillator_omega" not in slider_keys
    splitting = next(
        element for element in app.metric if element.label == r"Energy split $\Delta E_{01}$"
    )
    assert float(splitting.value) == pytest.approx(0.068624, abs=5e-5)
    assert splitting.delta == "+0.0%"
    assert any(
        r"V_0 = 4.0" in caption.value and "$d = 3.0$" in caption.value for caption in app.caption
    )
    assert any("tunneling pair" in element.value.lower() for element in app.markdown)


def test_double_well_tunneling_view_exposes_cycle_story_and_period() -> None:
    app = load_app()
    app.selectbox(key="experiment").set_value("Symmetric double well").run()

    assert app.segmented_control(key="visualization_mode").value == "Stationary state"

    app.segmented_control(key="visualization_mode").set_value("Tunneling motion").run()

    assert not app.exception
    slider_keys = {slider.key for slider in app.slider}
    assert "state_number" not in slider_keys
    assert "tunneling_cycle" in slider_keys
    assert "show_density" not in {toggle.key for toggle in app.toggle}
    assert "show_baseline" not in {toggle.key for toggle in app.toggle}
    metric_labels = [metric.label for metric in app.metric]
    assert metric_labels == [
        r"Energy split $\Delta E_{01}$",
        "Left probability",
        r"Period $T$",
    ]
    assert float(app.metric[1].value.rstrip("%")) == pytest.approx(99.6, abs=0.1)
    assert float(app.metric[2].value) == pytest.approx(91.56, abs=0.02)
    assert any("localized superposition" in element.value for element in app.markdown)
    assert any("half a period" in element.value for element in app.markdown)
    assert app.get("plotly_chart")

    app.slider(key="tunneling_cycle").set_value(0.5).run()

    assert not app.exception
    assert float(app.metric[1].value.rstrip("%")) == pytest.approx(0.4, abs=0.1)

    app.button(key="reset_controls").click().run()

    assert not app.exception
    assert app.segmented_control(key="visualization_mode").value == "Stationary state"
    assert app.slider(key="state_number").value == 1
    assert app.toggle(key="show_density").value is False
    assert app.toggle(key="show_baseline").value is True
    assert app.session_state["tunneling_cycle"] == pytest.approx(0.0)


def test_double_well_controls_update_current_result_against_stable_default() -> None:
    app = load_app()
    app.selectbox(key="experiment").set_value("Symmetric double well").run()

    app.slider(key="double_well_barrier_height").set_value(8.0).run()
    app.slider(key="double_well_separation").set_value(4.0).run()

    assert not app.exception
    splitting = next(
        element for element in app.metric if element.label == r"Energy split $\Delta E_{01}$"
    )
    assert float(splitting.value) == pytest.approx(0.000758, abs=1e-6)
    assert splitting.delta == "-98.9%"
    assert any(
        r"V_0 = 8.0" in caption.value and "$d = 4.0$" in caption.value for caption in app.caption
    )
    assert any(r"\Delta E_{01} = 0.068624" in caption.value for caption in app.caption)


def test_double_well_interaction_survives_switching_and_reset() -> None:
    app = load_app()
    app.selectbox(key="experiment").set_value("Symmetric double well").run()
    app.slider(key="double_well_barrier_height").set_value(8.0).run()
    app.slider(key="double_well_separation").set_value(4.0).run()
    app.slider(key="state_number").set_value(2).run()
    app.toggle(key="show_density").set_value(True).run()
    app.toggle(key="show_baseline").set_value(False).run()

    app.selectbox(key="experiment").set_value("Harmonic oscillator").run()
    app.selectbox(key="experiment").set_value("Symmetric double well").run()

    assert not app.exception
    assert app.slider(key="double_well_barrier_height").value == 8.0
    assert app.slider(key="double_well_separation").value == 4.0
    assert app.slider(key="state_number").value == 2
    assert app.toggle(key="show_density").value is True
    assert app.toggle(key="show_baseline").value is False
    splitting = next(
        element for element in app.metric if element.label == r"Energy split $\Delta E_{01}$"
    )
    assert not splitting.delta

    app.button(key="reset_controls").click().run()

    assert not app.exception
    assert app.slider(key="double_well_barrier_height").value == 4.0
    assert app.slider(key="double_well_separation").value == 3.0
    assert app.slider(key="state_number").value == 1
    assert app.toggle(key="show_density").value is False
    assert app.toggle(key="show_baseline").value is True


def test_reset_restores_every_interactive_default() -> None:
    app = load_app()
    app.slider(key="well_width").set_value(1.5).run()
    app.slider(key="grid_points").set_value(401).run()
    app.slider(key="state_number").set_value(5).run()
    app.toggle(key="show_density").set_value(True).run()

    app.button(key="reset_controls").click().run()

    assert not app.exception
    assert app.slider(key="well_width").value == 1.0
    assert app.slider(key="grid_points").value == 801
    assert app.slider(key="state_number").value == 1
    assert app.toggle(key="show_density").value is False
