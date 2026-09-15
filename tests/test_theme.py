import tomllib
from pathlib import Path

THEME_CONFIG = Path(__file__).parents[1] / ".streamlit" / "config.toml"


def test_theme_uses_a_distinct_scientific_typography_system() -> None:
    with THEME_CONFIG.open("rb") as config_file:
        theme = tomllib.load(config_file)["theme"]

    assert theme["font"].startswith("'IBM Plex Sans':")
    assert theme["headingFont"].startswith("'IBM Plex Serif':")
    assert theme["codeFont"].startswith("'IBM Plex Mono':")
    assert theme["baseFontSize"] == 16
    assert theme["baseFontWeight"] == 400
    assert theme["metricValueFontWeight"] == 500
    assert theme["headingFontWeights"] == [600, 600, 500, 500, 500, 500]
