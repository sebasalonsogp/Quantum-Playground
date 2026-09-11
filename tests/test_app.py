from pathlib import Path

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
