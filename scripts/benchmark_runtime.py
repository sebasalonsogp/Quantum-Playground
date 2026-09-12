"""Record representative uncached solver and Streamlit interaction timings."""

from argparse import ArgumentParser, ArgumentTypeError
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from statistics import median
from time import perf_counter

from streamlit.testing.v1 import AppTest

from quantum_playground.models import SimulationConfig
from quantum_playground.potentials import (
    create_double_well_config,
    create_harmonic_oscillator_config,
    create_infinite_well_config,
)
from quantum_playground.solver import solve

APP_PATH = Path(__file__).resolve().parents[1] / "app.py"
SOLVE_BUDGET_MS = 250.0
INTERACTION_BUDGET_MS = 1_000.0
DEFAULT_REPEATS = 5
_UNCACHED_WIDTHS = (0.5, 0.6, 0.7, 0.8, 0.9, 1.1, 1.2, 1.3, 1.4, 1.5)


@dataclass(frozen=True, slots=True)
class Measurement:
    """A named timing path evaluated against its product budget."""

    path: str
    samples_ms: tuple[float, ...]
    budget_ms: float

    @property
    def median_ms(self) -> float:
        return median(self.samples_ms)

    @property
    def maximum_ms(self) -> float:
        return max(self.samples_ms)


def _repeat_count(value: str) -> int:
    count = int(value)
    if not 1 <= count <= len(_UNCACHED_WIDTHS):
        raise ArgumentTypeError(f"repeats must be between 1 and {len(_UNCACHED_WIDTHS)}")
    return count


def _elapsed_ms(action: Callable[[], object]) -> float:
    start = perf_counter()
    action()
    return (perf_counter() - start) * 1_000.0


def _measure_solver(
    path: str,
    config: SimulationConfig,
    repeats: int,
) -> Measurement:
    samples = tuple(solve(config).solve_time_seconds * 1_000.0 for _ in range(repeats))
    return Measurement(path, samples, SOLVE_BUDGET_MS)


def _require_clean_app(app: AppTest, path: str) -> None:
    if app.exception:
        raise RuntimeError(f"{path} produced an app exception: {app.exception[0].message}")


def _measure_app(repeats: int) -> list[Measurement]:
    app = AppTest.from_file(APP_PATH, default_timeout=10)
    initial_ms = _elapsed_ms(app.run)
    _require_clean_app(app, "App initial render")

    warm_samples = []
    for index in range(repeats):
        app.toggle(key="show_density").set_value(index % 2 == 0)
        warm_samples.append(_elapsed_ms(app.run))
        _require_clean_app(app, "App cached visual interaction")

    uncached_samples = []
    for width in _UNCACHED_WIDTHS[:repeats]:
        app.slider(key="well_width").set_value(width)
        uncached_samples.append(_elapsed_ms(app.run))
        _require_clean_app(app, "App uncached physical interaction")

    return [
        Measurement("App initial render", (initial_ms,), INTERACTION_BUDGET_MS),
        Measurement(
            "App cached visual interaction",
            tuple(warm_samples),
            INTERACTION_BUDGET_MS,
        ),
        Measurement(
            "App uncached physical interaction",
            tuple(uncached_samples),
            INTERACTION_BUDGET_MS,
        ),
    ]


def _solver_cases() -> tuple[tuple[str, SimulationConfig], ...]:
    return (
        ("Solve infinite well default", create_infinite_well_config()),
        (
            "Solve infinite well stress",
            create_infinite_well_config(width=0.5, grid_points=1_201),
        ),
        ("Solve harmonic default", create_harmonic_oscillator_config()),
        (
            "Solve harmonic stress",
            create_harmonic_oscillator_config(omega=0.5, grid_points=1_601),
        ),
        ("Solve double well default", create_double_well_config()),
        (
            "Solve double well stress",
            create_double_well_config(
                barrier_height=8.0,
                well_separation=4.0,
                grid_points=1_601,
            ),
        ),
    )


def _print_report(measurements: list[Measurement], repeats: int) -> None:
    print(f"Quantum Playground runtime benchmark ({repeats} repeated samples where applicable)")
    print(f"{'Path':38} {'Median':>10} {'Maximum':>10} {'Budget':>10}  Result")
    for measurement in measurements:
        within_budget = measurement.maximum_ms <= measurement.budget_ms
        result = "PASS" if within_budget else "EXPLAIN"
        print(
            f"{measurement.path:38} "
            f"{measurement.median_ms:9.1f}ms "
            f"{measurement.maximum_ms:9.1f}ms "
            f"{measurement.budget_ms:9.0f}ms  "
            f"{result}"
        )


def main() -> None:
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--repeats", type=_repeat_count, default=DEFAULT_REPEATS)
    repeats = parser.parse_args().repeats

    measurements = _measure_app(repeats)
    measurements.extend(_measure_solver(path, config, repeats) for path, config in _solver_cases())
    _print_report(measurements, repeats)


if __name__ == "__main__":
    main()
