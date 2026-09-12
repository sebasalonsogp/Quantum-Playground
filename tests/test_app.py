from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

APP_PATH = Path(__file__).parents[1] / "app.py"
DEFAULT_TIMEOUT = 10


def load_app() -> AppTest:
    return AppTest.from_file(APP_PATH, default_timeout=DEFAULT_TIMEOUT).run()


def test_app_loads_with_project_identity() -> None:
    app = load_app()

    assert not app.exception
    assert app.title[0].value == "Quantum Playground"
    assert app.selectbox(key="experiment").value == "Infinite square well"
    assert app.slider(key="well_width").value == 1.0
    assert app.slider(key="grid_points").value == 801
    assert app.slider(key="state_number").value == 1
    assert app.toggle(key="show_density").value is False
    assert any(element.label == "Selected energy E1" for element in app.metric)
    assert app.success


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
    assert float(updated_error) > float(initial_error)


def test_state_selection_and_density_toggle_update_the_explanation() -> None:
    app = load_app()

    app.slider(key="state_number").set_value(4).run()
    app.toggle(key="show_density").set_value(True).run()

    assert not app.exception
    assert any(element.label == "Selected energy E4" for element in app.metric)
    assert any("3 internal nodes" in element.value for element in app.markdown)
    assert any("probability density" in element.value.lower() for element in app.markdown)


def test_switching_to_harmonic_updates_controls_result_and_explanation() -> None:
    app = load_app()

    app.selectbox(key="experiment").set_value("Harmonic oscillator").run()

    assert not app.exception
    assert app.slider(key="oscillator_omega").value == 1.0
    slider_keys = {slider.key for slider in app.slider}
    assert "well_width" not in slider_keys
    assert "grid_points" not in slider_keys
    assert any(subheader.value == "Harmonic oscillator" for subheader in app.subheader)
    selected_energy = next(
        element.value for element in app.metric if element.label == "Selected energy E1"
    )
    assert float(selected_energy) == pytest.approx(0.5, abs=1e-4)
    assert any("evenly spaced" in element.value for element in app.markdown)
    assert any("1,201 grid points" in caption.value for caption in app.caption)


def test_harmonic_frequency_changes_spacing_and_reset() -> None:
    app = load_app()
    app.selectbox(key="experiment").set_value("Harmonic oscillator").run()
    initial_energy = next(
        element.value for element in app.metric if element.label == "Selected energy E1"
    )

    app.slider(key="oscillator_omega").set_value(2.0).run()

    updated_energy = next(
        element.value for element in app.metric if element.label == "Selected energy E1"
    )
    assert float(updated_energy) == pytest.approx(2.0 * float(initial_energy), abs=1e-4)
    assert any("ω = 2.0" in caption.value for caption in app.caption)

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
    splitting = next(element for element in app.metric if element.label == "Tunneling split ΔE₀₁")
    assert float(splitting.value) == pytest.approx(0.068624, abs=1e-6)
    assert splitting.delta == "+0.0%"
    assert any("fixed at V₀ = 4.0 and d = 3.0" in caption.value for caption in app.caption)
    assert any("tunneling pair" in element.value.lower() for element in app.markdown)


def test_double_well_controls_update_current_result_against_stable_default() -> None:
    app = load_app()
    app.selectbox(key="experiment").set_value("Symmetric double well").run()

    app.slider(key="double_well_barrier_height").set_value(8.0).run()
    app.slider(key="double_well_separation").set_value(4.0).run()

    assert not app.exception
    splitting = next(element for element in app.metric if element.label == "Tunneling split ΔE₀₁")
    assert float(splitting.value) == pytest.approx(0.000758, abs=1e-6)
    assert splitting.delta == "-98.9%"
    assert any(
        "V₀ = 8.0" in caption.value and "d = 4.0" in caption.value for caption in app.caption
    )
    assert any("ΔE₀₁ = 0.068624" in caption.value for caption in app.caption)


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
    splitting = next(element for element in app.metric if element.label == "Tunneling split ΔE₀₁")
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
