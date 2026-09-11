from pathlib import Path

from streamlit.testing.v1 import AppTest

APP_PATH = Path(__file__).parents[1] / "app.py"


def test_app_loads_with_project_identity() -> None:
    app = AppTest.from_file(APP_PATH).run()

    assert not app.exception
    assert app.title[0].value == "Quantum Playground"
