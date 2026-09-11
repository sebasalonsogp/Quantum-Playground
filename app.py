"""Streamlit entrypoint for Quantum Playground."""

import streamlit as st

from quantum_playground import __version__
from quantum_playground.figures import StateQuantity, build_stationary_state_figure
from quantum_playground.models import SimulationResult
from quantum_playground.potentials import INFINITE_WELL_PRESET, WIDTH, create_infinite_well_config
from quantum_playground.solver import solve
from quantum_playground.validation import validate_infinite_well

_DEFAULT_CONTROLS = {
    "well_width": WIDTH.default,
    "grid_points": INFINITE_WELL_PRESET.default_grid_points,
    "state_number": 1,
    "show_density": False,
}


def _reset_controls() -> None:
    for key, value in _DEFAULT_CONTROLS.items():
        st.session_state[key] = value


@st.cache_data(show_spinner=False, max_entries=16)
def _run_simulation(width: float, grid_points: int) -> SimulationResult:
    config = create_infinite_well_config(width=width, grid_points=grid_points)
    return solve(config)


st.set_page_config(
    page_title="Quantum Playground",
    page_icon=":material/science:",
    layout="wide",
    initial_sidebar_state="expanded",
)

for control_key, default_value in _DEFAULT_CONTROLS.items():
    st.session_state.setdefault(control_key, default_value)

with st.sidebar:
    st.header("Experiment setup", icon=":material/tune:")
    st.selectbox(
        "Experiment",
        (INFINITE_WELL_PRESET.title,),
        key="experiment",
        disabled=True,
        help="The harmonic oscillator and double well arrive in the next project phase.",
    )
    well_width = st.slider(
        WIDTH.label,
        min_value=WIDTH.minimum,
        max_value=WIDTH.maximum,
        step=WIDTH.step,
        key="well_width",
        help=WIDTH.help_text,
    )
    grid_points = st.slider(
        "Grid resolution",
        min_value=INFINITE_WELL_PRESET.minimum_grid_points,
        max_value=INFINITE_WELL_PRESET.maximum_grid_points,
        step=INFINITE_WELL_PRESET.grid_step,
        key="grid_points",
        help="More points reduce discretization error but require more computation.",
    )
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
    "Explore a real sparse-matrix eigensolver, then inspect the numerical evidence behind its "
    "result. No quantum mechanics background is required."
)

st.subheader(INFINITE_WELL_PRESET.title)
st.markdown(
    f"{INFINITE_WELL_PRESET.description} **Try this:** choose a higher state and count its "
    "internal nodes, or widen the well and watch every energy level move downward."
)

control_columns = st.columns((3, 2), vertical_alignment="bottom")
with control_columns[0]:
    state_number = st.slider(
        "Quantum state",
        min_value=1,
        max_value=INFINITE_WELL_PRESET.default_eigenstate_count,
        step=1,
        key="state_number",
        help="State n has n − 1 internal nodes and an energy proportional to n².",
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
        result = _run_simulation(float(well_width), int(grid_points))
except ValueError as error:
    result_slot.error(
        f"The selected controls could not produce a valid simulation: {error}",
        icon=":material/error:",
    )
    st.stop()

report = validate_infinite_well(result)
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
    st.caption(
        f"Solved {result.config.eigenstate_count} states "
        f"on {result.config.grid_points} grid points "
        f"across a width of {well_width:.1f}. The upper state profile is display-scaled; the lower "
        "panel shows its true numerical values."
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
    st.markdown(
        f"State **n = {state_number}** has **{state_number - 1} internal nodes**. Its energy is "
        f"approximately proportional to **n²**, so higher states spread farther apart on the "
        "energy axis."
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
    st.caption("Dimensionless convention: ℏ = m = 1. Boundary condition: ψ = 0 at both walls.")
    st.table(
        {
            "State": [f"n = {index}" for index in range(1, result.config.eigenstate_count + 1)],
            "Numerical E": [f"{energy:.7f}" for energy in result.energies],
            "Exact E": [f"{energy:.7f}" for energy in report.analytic_energies],
            "Relative error": [f"{error:.2e}" for error in report.relative_energy_errors],
        }
    )
    st.caption(
        "Validation limits: energy error ≤ 1e−4, residual ≤ 1e−8, normalization and "
        "orthogonality errors ≤ 1e−12."
    )

st.caption(f"Quantum Playground v{__version__} · Python, NumPy, SciPy, Plotly, and Streamlit")
