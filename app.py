"""Streamlit entrypoint for Quantum Playground."""

import streamlit as st

from quantum_playground import __version__
from quantum_playground.figures import StateQuantity, build_stationary_state_figure
from quantum_playground.models import ExperimentId, SimulationConfig, SimulationResult
from quantum_playground.potentials import (
    HARMONIC_OSCILLATOR_PRESET,
    INFINITE_WELL_PRESET,
    OMEGA,
    WIDTH,
    create_harmonic_oscillator_config,
    create_infinite_well_config,
)
from quantum_playground.solver import solve
from quantum_playground.validation import (
    ValidationReport,
    validate_harmonic_oscillator,
    validate_infinite_well,
)

_EXPERIMENTS = {
    INFINITE_WELL_PRESET.title: ExperimentId.INFINITE_WELL,
    HARMONIC_OSCILLATOR_PRESET.title: ExperimentId.HARMONIC_OSCILLATOR,
}

_DEFAULT_CONTROLS = {
    "well_width": WIDTH.default,
    "grid_points": INFINITE_WELL_PRESET.default_grid_points,
    "oscillator_omega": OMEGA.default,
    "state_number": 1,
    "show_density": False,
}
_DYNAMIC_CONTROL_KEYS = ("well_width", "grid_points", "oscillator_omega")


def _saved_control_key(key: str) -> str:
    return f"saved_{key}"


def _load_dynamic_control(key: str) -> None:
    st.session_state[key] = st.session_state[_saved_control_key(key)]


def _store_dynamic_control(key: str) -> None:
    st.session_state[_saved_control_key(key)] = st.session_state[key]


def _reset_controls() -> None:
    for key in _DYNAMIC_CONTROL_KEYS:
        default_value = _DEFAULT_CONTROLS[key]
        st.session_state[_saved_control_key(key)] = default_value
        if key in st.session_state:
            st.session_state[key] = default_value
    for key in ("state_number", "show_density"):
        st.session_state[key] = _DEFAULT_CONTROLS[key]


@st.cache_data(show_spinner=False, max_entries=16)
def _run_simulation(config: SimulationConfig) -> SimulationResult:
    return solve(config)


def _validate_result(result: SimulationResult) -> ValidationReport:
    if result.config.experiment is ExperimentId.INFINITE_WELL:
        return validate_infinite_well(result)
    if result.config.experiment is ExperimentId.HARMONIC_OSCILLATOR:
        return validate_harmonic_oscillator(result)
    raise ValueError(f"no validation pipeline for {result.config.experiment.value!r}")


st.set_page_config(
    page_title="Quantum Playground",
    page_icon=":material/science:",
    layout="wide",
    initial_sidebar_state="expanded",
)

for control_key, default_value in _DEFAULT_CONTROLS.items():
    state_key = (
        _saved_control_key(control_key) if control_key in _DYNAMIC_CONTROL_KEYS else control_key
    )
    st.session_state.setdefault(state_key, default_value)

with st.sidebar:
    st.header("Experiment setup", icon=":material/tune:")
    experiment_title = st.selectbox(
        "Experiment",
        tuple(_EXPERIMENTS),
        key="experiment",
        help="Switch experiments without leaving the shared numerical workflow.",
    )
    experiment = _EXPERIMENTS[experiment_title]
    if experiment is ExperimentId.INFINITE_WELL:
        _load_dynamic_control("well_width")
        well_width = st.slider(
            WIDTH.label,
            min_value=WIDTH.minimum,
            max_value=WIDTH.maximum,
            step=WIDTH.step,
            key="well_width",
            help=WIDTH.help_text,
            on_change=_store_dynamic_control,
            args=("well_width",),
        )
        _load_dynamic_control("grid_points")
        grid_points = st.slider(
            "Grid resolution",
            min_value=INFINITE_WELL_PRESET.minimum_grid_points,
            max_value=INFINITE_WELL_PRESET.maximum_grid_points,
            step=INFINITE_WELL_PRESET.grid_step,
            key="grid_points",
            help="More points reduce discretization error but require more computation.",
            on_change=_store_dynamic_control,
            args=("grid_points",),
        )
        config = create_infinite_well_config(
            width=float(well_width),
            grid_points=int(grid_points),
        )
    else:
        _load_dynamic_control("oscillator_omega")
        oscillator_omega = st.slider(
            OMEGA.label,
            min_value=OMEGA.minimum,
            max_value=OMEGA.maximum,
            step=OMEGA.step,
            key="oscillator_omega",
            help=OMEGA.help_text,
            on_change=_store_dynamic_control,
            args=("oscillator_omega",),
        )
        config = create_harmonic_oscillator_config(omega=float(oscillator_omega))
        st.caption("Uses a fixed, validated domain and resolution so frequency stays the focus.")
    st.button(
        "Reset experiment",
        key="reset_controls",
        icon=":material/refresh:",
        on_click=_reset_controls,
        width="stretch",
    )
    st.caption("Controls are bounded to keep every simulation physically and numerically valid.")

st.title("Quantum Playground", icon=":material/science:")
st.caption(
    "Explore how confinement shapes quantum states with a real sparse-matrix eigensolver, then "
    "inspect the numerical evidence behind each result."
)

if experiment is ExperimentId.INFINITE_WELL:
    preset = INFINITE_WELL_PRESET
    try_this = (
        "Choose a higher state and count its internal nodes, or widen the well and watch every "
        "energy level move downward."
    )
    state_help = "State n has n − 1 internal nodes and an energy proportional to n²."
else:
    preset = HARMONIC_OSCILLATOR_PRESET
    try_this = (
        "Raise ω and watch the evenly spaced energy ladder expand while the state contracts "
        "toward the center."
    )
    state_help = "Displayed state k corresponds to oscillator quantum number n = k − 1."

st.subheader(preset.title)
st.markdown(f"{preset.description} **Try this:** {try_this}")

control_columns = st.columns((3, 2), vertical_alignment="bottom")
with control_columns[0]:
    state_number = st.slider(
        "Quantum state",
        min_value=1,
        max_value=preset.default_eigenstate_count,
        step=1,
        key="state_number",
        help=state_help,
    )
with control_columns[1]:
    show_density = st.toggle(
        "Show probability density",
        key="show_density",
        help="Switch from the signed wavefunction ψ(x) to the measurable density |ψ(x)|².",
    )

result_slot = st.container()

try:
    with result_slot, st.spinner("Solving the stationary Schrödinger equation…"):
        result = _run_simulation(config)
except ValueError as error:
    result_slot.error(
        f"The selected controls could not produce a valid simulation: {error}",
        icon=":material/error:",
    )
    st.stop()

report = _validate_result(result)
selected_index = int(state_number) - 1
quantity = StateQuantity.PROBABILITY_DENSITY if show_density else StateQuantity.WAVEFUNCTION

with result_slot:
    metric_columns = st.columns(4)
    metric_columns[0].metric(
        f"Selected energy E{state_number}",
        f"{result.energies[selected_index]:.5f}",
    )
    metric_columns[1].metric(
        "Analytic energy error",
        f"{report.relative_energy_errors[selected_index]:.2e}",
    )
    metric_columns[2].metric(
        "Maximum residual",
        f"{report.maximum_relative_residual:.2e}",
    )
    metric_columns[3].metric("Solve time", f"{result.solve_time_seconds * 1_000:.0f} ms")

    figure = build_stationary_state_figure(
        result,
        state_index=selected_index,
        quantity=quantity,
    )
    st.plotly_chart(
        figure,
        key="stationary_state_figure",
        width="stretch",
        theme=None,
        config={"displaylogo": False, "scrollZoom": False, "responsive": True},
    )
    if experiment is ExperimentId.INFINITE_WELL:
        simulation_summary = f"across a width of {well_width:.1f}"
    else:
        simulation_summary = f"on x ∈ [−8, 8] with ω = {oscillator_omega:.1f}"
    st.caption(
        f"Solved {result.config.eigenstate_count} states on "
        f"{result.config.grid_points:,} grid points {simulation_summary}. The upper state profile "
        "is display-scaled; the lower panel shows its true numerical values."
    )
    if report.passed:
        st.success(
            "Validation passed — analytic energies, residuals, normalization, and orthogonality "
            "all meet the documented tolerances.",
            icon=":material/verified:",
        )
    else:
        st.error(
            "This result did not pass every numerical validation check. Inspect the details below.",
            icon=":material/error:",
        )

explanation_title = (
    "Reading the probability density" if show_density else "Reading the wavefunction"
)
with st.container(border=True):
    st.subheader(explanation_title, icon=":material/lightbulb:")
    if experiment is ExperimentId.INFINITE_WELL:
        st.markdown(
            f"State **n = {state_number}** has **{state_number - 1} internal nodes**. Its energy "
            "is proportional to **n²**, so higher states spread farther apart on the energy axis."
        )
    else:
        oscillator_index = int(state_number) - 1
        st.markdown(
            f"Displayed state **{state_number}** is oscillator state **n = {oscillator_index}** "
            f"and has **{oscillator_index} internal nodes**. Adjacent energies are evenly spaced "
            f"by **ΔE = ω = {oscillator_omega:.1f}**, including the nonzero ground-state energy."
        )
    if show_density:
        st.markdown(
            "The probability density is never negative. Peaks mark positions where the particle "
            "is more likely to be found; nodes remain positions of zero probability."
        )
    else:
        st.markdown(
            "The wavefunction changes sign between nodes. That sign carries phase information, "
            "while the squared magnitude determines measurement probability."
        )

with st.expander("Numerical details", icon=":material/functions:"):
    st.markdown(
        "A second-order centered finite difference represents the kinetic-energy operator, and "
        "SciPy solves the resulting real symmetric sparse eigenproblem."
    )
    st.latex(r"-\frac{1}{2}\frac{d^2\psi}{dx^2} + V(x)\psi = E\psi")
    if experiment is ExperimentId.INFINITE_WELL:
        st.latex(r"V(x)=0,\qquad E_n=\frac{\pi^2 n^2}{2L^2},\quad n=1,2,\ldots")
        st.caption("Dimensionless convention: ℏ = m = 1. Boundary condition: ψ = 0 at both walls.")
        state_labels = [f"n = {index}" for index in range(1, result.config.eigenstate_count + 1)]
    else:
        st.latex(r"V(x)=\frac{1}{2}\omega^2x^2,\qquad E_n=\omega(n+\tfrac{1}{2})")
        st.caption(
            "Dimensionless convention: ℏ = m = 1. The unbounded oscillator is approximated on "
            "x ∈ [−8, 8] with ψ = 0 at both endpoints."
        )
        state_labels = [
            f"n = {index} (state {index + 1})" for index in range(result.config.eigenstate_count)
        ]
    st.table(
        {
            "State": state_labels,
            "Numerical E": [f"{energy:.7f}" for energy in result.energies],
            "Exact E": [f"{energy:.7f}" for energy in report.analytic_energies],
            "Relative error": [f"{error:.2e}" for error in report.relative_energy_errors],
        }
    )
    st.caption(
        f"Validation limits: energy error ≤ {report.relative_energy_tolerance:.1e}, residual ≤ "
        "1e−8, normalization and orthogonality errors ≤ 1e−12."
    )

st.caption(f"Quantum Playground v{__version__} · Python, NumPy, SciPy, Plotly, and Streamlit")
