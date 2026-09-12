"""Streamlit entrypoint for Quantum Playground."""

import streamlit as st

from quantum_playground import __version__
from quantum_playground.figures import StateQuantity, build_stationary_state_figure
from quantum_playground.models import ExperimentId, SimulationConfig, SimulationResult
from quantum_playground.potentials import (
    BARRIER_HEIGHT,
    DOUBLE_WELL_PRESET,
    HARMONIC_OSCILLATOR_PRESET,
    INFINITE_WELL_PRESET,
    OMEGA,
    WELL_SEPARATION,
    WIDTH,
    create_double_well_config,
    create_harmonic_oscillator_config,
    create_infinite_well_config,
)
from quantum_playground.solver import solve
from quantum_playground.validation import (
    MAX_NORMALIZATION_ERROR,
    MAX_ORTHOGONALITY_ERROR,
    MAX_RELATIVE_RESIDUAL,
    ValidationReport,
    assess_infinite_well_convergence,
    validate_harmonic_oscillator,
    validate_infinite_well,
)

_EXPERIMENTS = {
    INFINITE_WELL_PRESET.title: ExperimentId.INFINITE_WELL,
    HARMONIC_OSCILLATOR_PRESET.title: ExperimentId.HARMONIC_OSCILLATOR,
    DOUBLE_WELL_PRESET.title: ExperimentId.DOUBLE_WELL,
}

_DEFAULT_CONTROLS = {
    "well_width": WIDTH.default,
    "grid_points": INFINITE_WELL_PRESET.default_grid_points,
    "oscillator_omega": OMEGA.default,
    "double_well_barrier_height": BARRIER_HEIGHT.default,
    "double_well_separation": WELL_SEPARATION.default,
    "show_baseline": True,
    "state_number": 1,
    "show_density": False,
}
_DYNAMIC_CONTROL_KEYS = (
    "well_width",
    "grid_points",
    "oscillator_omega",
    "double_well_barrier_height",
    "double_well_separation",
    "show_baseline",
)
_CONVERGENCE_GRID_POINTS = (201, 401, 801)


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


def _validate_result(result: SimulationResult) -> ValidationReport | None:
    if result.config.experiment is ExperimentId.INFINITE_WELL:
        return validate_infinite_well(result)
    if result.config.experiment is ExperimentId.HARMONIC_OSCILLATOR:
        return validate_harmonic_oscillator(result)
    if result.config.experiment is ExperimentId.DOUBLE_WELL:
        return None
    raise ValueError(f"no validation pipeline for {result.config.experiment.value!r}")


def _diagnostic_checks(
    result: SimulationResult,
    report: ValidationReport | None,
) -> list[tuple[str, float, float, bool]]:
    if report is None:
        diagnostics = result.diagnostics
        residual = float(max(diagnostics.residual_norms))
        normalization = float(max(diagnostics.normalization_errors))
        orthogonality = diagnostics.orthogonality_error
        checks = []
    else:
        residual = report.maximum_relative_residual
        normalization = report.maximum_normalization_error
        orthogonality = report.orthogonality_error
        checks = [
            (
                "Analytic energy",
                report.maximum_relative_energy_error,
                report.relative_energy_tolerance,
                report.energy_accurate,
            )
        ]

    checks.extend(
        (
            (
                "Eigenpair residual",
                residual,
                MAX_RELATIVE_RESIDUAL,
                residual <= MAX_RELATIVE_RESIDUAL,
            ),
            (
                "Wavefunction normalization",
                normalization,
                MAX_NORMALIZATION_ERROR,
                normalization <= MAX_NORMALIZATION_ERROR,
            ),
            (
                "State orthogonality",
                orthogonality,
                MAX_ORTHOGONALITY_ERROR,
                orthogonality <= MAX_ORTHOGONALITY_ERROR,
            ),
        )
    )
    return checks


def _diagnostic_evidence(
    checks: list[tuple[str, float, float, bool]],
) -> dict[str, list[str]]:
    return {
        "Check": [label for label, _, _, _ in checks],
        "Observed": [f"{observed:.2e}" for _, observed, _, _ in checks],
        "Limit": [f"≤ {limit:.1e}" for _, _, limit, _ in checks],
        "Status": [
            ":green-badge[Pass]" if passed else ":red-badge[Fail]" for _, _, _, passed in checks
        ],
    }


st.set_page_config(
    page_title="Quantum Playground",
    page_icon=":material/science:",
    layout="wide",
    initial_sidebar_state="auto",
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
    elif experiment is ExperimentId.HARMONIC_OSCILLATOR:
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
    else:
        _load_dynamic_control("double_well_barrier_height")
        double_well_barrier_height = st.slider(
            BARRIER_HEIGHT.label,
            min_value=BARRIER_HEIGHT.minimum,
            max_value=BARRIER_HEIGHT.maximum,
            step=BARRIER_HEIGHT.step,
            key="double_well_barrier_height",
            help=BARRIER_HEIGHT.help_text,
            on_change=_store_dynamic_control,
            args=("double_well_barrier_height",),
        )
        _load_dynamic_control("double_well_separation")
        double_well_separation = st.slider(
            WELL_SEPARATION.label,
            min_value=WELL_SEPARATION.minimum,
            max_value=WELL_SEPARATION.maximum,
            step=WELL_SEPARATION.step,
            key="double_well_separation",
            help=WELL_SEPARATION.help_text,
            on_change=_store_dynamic_control,
            args=("double_well_separation",),
        )
        config = create_double_well_config(
            barrier_height=float(double_well_barrier_height),
            well_separation=float(double_well_separation),
        )
        st.caption("The fixed domain and resolution keep both low states below the barrier.")
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
elif experiment is ExperimentId.HARMONIC_OSCILLATOR:
    preset = HARMONIC_OSCILLATOR_PRESET
    try_this = (
        "Raise ω and watch the evenly spaced energy ladder expand while the state contracts "
        "toward the center."
    )
    state_help = "Displayed state k corresponds to oscillator quantum number n = k − 1."
else:
    preset = DOUBLE_WELL_PRESET
    try_this = (
        "Raise either control and watch ΔE₀₁ collapse as the lowest tunneling pair becomes "
        "nearly degenerate."
    )
    state_help = "States 1 and 2 are the even/odd tunneling pair; higher states add nodes."

st.header(preset.title)
st.markdown(f"{preset.description} **Try this:** {try_this}")
st.markdown("**Explore this state**")
st.caption("Results update automatically when you change a control.")

control_columns = st.columns((3, 2, 2), vertical_alignment="bottom")
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
        wrap=True,
    )
with control_columns[2]:
    if experiment is ExperimentId.DOUBLE_WELL:
        _load_dynamic_control("show_baseline")
        show_baseline = st.toggle(
            "Compare with default",
            key="show_baseline",
            help="Hold the default potential and lowest pair fixed behind the current result.",
            on_change=_store_dynamic_control,
            args=("show_baseline",),
            wrap=True,
        )
    else:
        show_baseline = False

st.subheader("Live result", icon=":material/insights:")
result_slot = st.container()
comparison_result = None

try:
    with result_slot, st.spinner("Solving the stationary Schrödinger equation…"):
        result = _run_simulation(config)
        if experiment is ExperimentId.DOUBLE_WELL and show_baseline:
            comparison_result = _run_simulation(create_double_well_config())
except ValueError as error:
    result_slot.error(
        f"The selected controls could not produce a valid simulation: {error}",
        icon=":material/error:",
    )
    st.stop()

report = _validate_result(result)
diagnostic_checks = _diagnostic_checks(result, report)
selected_index = int(state_number) - 1
quantity = StateQuantity.PROBABILITY_DENSITY if show_density else StateQuantity.WAVEFUNCTION

with result_slot:
    if experiment is ExperimentId.DOUBLE_WELL:
        splitting = float(result.energies[1] - result.energies[0])
        splitting_delta = None
        if comparison_result is not None:
            reference_splitting = float(
                comparison_result.energies[1] - comparison_result.energies[0]
            )
            splitting_delta = f"{100.0 * (splitting / reference_splitting - 1.0):+.1f}%"
        with st.container(horizontal=True, gap="small"):
            st.metric(
                "Tunneling split ΔE₀₁",
                f"{splitting:.6f}",
                delta=splitting_delta,
                delta_color="off",
                delta_arrow="off",
                delta_description="vs default" if comparison_result is not None else None,
                help="Energy gap between the even ground state and odd first excited state.",
                border=True,
            )
            st.metric(
                f"Selected energy E{state_number}",
                f"{result.energies[selected_index]:.5f}",
                border=True,
            )
            st.metric(
                "Solve time",
                f"{result.solve_time_seconds * 1_000:.0f} ms",
                border=True,
            )
    else:
        with st.container(horizontal=True, gap="small"):
            st.metric(
                f"Selected energy E{state_number}",
                f"{result.energies[selected_index]:.5f}",
                border=True,
            )
            st.metric(
                "Analytic energy error",
                f"{report.relative_energy_errors[selected_index]:.2e}",
                border=True,
            )
            st.metric(
                "Solve time",
                f"{result.solve_time_seconds * 1_000:.0f} ms",
                border=True,
            )

    figure = build_stationary_state_figure(
        result,
        state_index=selected_index,
        quantity=quantity,
        comparison_result=comparison_result,
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
    elif experiment is ExperimentId.HARMONIC_OSCILLATOR:
        simulation_summary = f"on x ∈ [−8, 8] with ω = {oscillator_omega:.1f}"
    else:
        simulation_summary = (
            f"on x ∈ [−6, 6] with V₀ = {double_well_barrier_height:.1f} and "
            f"d = {double_well_separation:.1f}"
        )
    st.caption(
        f"Solved {result.config.eigenstate_count} states on "
        f"{result.config.grid_points:,} grid points {simulation_summary}. The upper state profile "
        "is display-scaled; the lower panel shows its true numerical values."
    )
    if comparison_result is not None:
        reference_splitting = float(comparison_result.energies[1] - comparison_result.energies[0])
        st.caption(
            f"The default reference is fixed at V₀ = {BARRIER_HEIGHT.default:.1f} and "
            f"d = {WELL_SEPARATION.default:.1f} (ΔE₀₁ = {reference_splitting:.6f}). Dashed "
            "potential and dotted energy levels stay fixed while solid traces follow your controls."
        )
    result_passed = all(passed for _, _, _, passed in diagnostic_checks)
    if result_passed:
        st.badge(
            "Numerically verified",
            icon=":material/verified:",
            color="green",
            help="All applicable checks are within the documented limits.",
        )
        st.caption(
            "Analytic agreement and numerical consistency checks passed."
            if report is not None
            else "Residual, normalization, and orthogonality checks passed."
        )
    else:
        st.badge(
            "Verification failed",
            icon=":material/error:",
            color="red",
        )
        st.error(
            "Do not treat this result as validated. At least one numerical check exceeds its "
            "documented limit; inspect Numerical details below.",
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
    elif experiment is ExperimentId.HARMONIC_OSCILLATOR:
        oscillator_index = int(state_number) - 1
        st.markdown(
            f"Displayed state **{state_number}** is oscillator state **n = {oscillator_index}** "
            f"and has **{oscillator_index} internal nodes**. Adjacent energies are evenly spaced "
            f"by **ΔE = ω = {oscillator_omega:.1f}**, including the nonzero ground-state energy."
        )
    else:
        parity = "even" if selected_index % 2 == 0 else "odd"
        st.markdown(
            f"Displayed state **{state_number}** has **{parity} parity**. The lowest even and odd "
            f"states form a tunneling pair with **ΔE₀₁ = {splitting:.6f}**; a smaller split means "
            "the particle exchanges between the wells more slowly."
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
    st.markdown("**Method and discretization**")
    st.markdown(
        "A second-order centered finite difference represents the kinetic-energy operator, and "
        "SciPy solves the resulting real symmetric sparse eigenproblem."
    )
    st.latex(r"-\frac{1}{2}\frac{d^2\psi}{dx^2} + V(x)\psi = E\psi")
    if experiment is ExperimentId.INFINITE_WELL:
        st.latex(r"V(x)=0,\qquad E_n=\frac{\pi^2 n^2}{2L^2},\quad n=1,2,\ldots")
        boundary_description = "ψ = 0 at both walls"
        state_labels = [f"n = {index}" for index in range(1, result.config.eigenstate_count + 1)]
    elif experiment is ExperimentId.HARMONIC_OSCILLATOR:
        st.latex(r"V(x)=\frac{1}{2}\omega^2x^2,\qquad E_n=\omega(n+\tfrac{1}{2})")
        boundary_description = (
            "finite-domain approximation on x ∈ [−8, 8], with ψ = 0 at both endpoints"
        )
        state_labels = [
            f"n = {index} (state {index + 1})" for index in range(result.config.eigenstate_count)
        ]
    else:
        st.latex(r"V(x)=V_0\left[\left(\frac{2x}{d}\right)^2-1\right]^2")
        boundary_description = "finite domain x ∈ [−6, 6], with ψ = 0 at both endpoints"
        state_labels = [
            f"state {index + 1} · {'even' if index % 2 == 0 else 'odd'}"
            for index in range(result.config.eigenstate_count)
        ]
    grid_spacing = float(result.x[1] - result.x[0])
    st.caption(
        f"Grid: {result.config.grid_points:,} points with Δx = {grid_spacing:.3e}. "
        f"Dimensionless units: ℏ = m = 1. Boundary: {boundary_description}."
    )
    if experiment is ExperimentId.DOUBLE_WELL:
        st.caption("The minima lie at x = ±d/2 and the central barrier is V(0) = V₀.")

    st.markdown("**Current-run checks**")
    st.table(_diagnostic_evidence(diagnostic_checks), border="horizontal")

    st.markdown("**Energy spectrum**")
    if report is not None:
        st.table(
            {
                "State": state_labels,
                "Numerical E": [f"{energy:.7f}" for energy in result.energies],
                "Exact E": [f"{energy:.7f}" for energy in report.analytic_energies],
                "Relative error": [f"{error:.2e}" for error in report.relative_energy_errors],
            },
            border="horizontal",
        )
    else:
        gaps = ["—", *(f"{gap:.7f}" for gap in result.energies[1:] - result.energies[:-1])]
        st.table(
            {
                "State and parity": state_labels,
                "Numerical E": [f"{energy:.7f}" for energy in result.energies],
                "Gap from previous": gaps,
            },
            border="horizontal",
        )
        st.caption(
            "No elementary exact spectrum is used for this potential, so the app makes no analytic "
            "accuracy claim for these energies."
        )

    if experiment is ExperimentId.INFINITE_WELL:
        st.markdown("**Grid-refinement check**")
        st.caption(
            "Run the ground state on three successively finer grids. A second-order finite "
            "difference should reduce energy error at an observed order near 2."
        )
        if st.button(
            "Run convergence check",
            key="run_convergence",
            icon=":material/query_stats:",
        ):
            with st.spinner("Running three-grid convergence check…"):
                convergence_results = tuple(
                    _run_simulation(
                        create_infinite_well_config(
                            width=float(well_width),
                            grid_points=grid_points,
                            eigenstate_count=1,
                        )
                    )
                    for grid_points in _CONVERGENCE_GRID_POINTS
                )
                convergence = assess_infinite_well_convergence(convergence_results)
            if convergence.passed:
                st.badge(
                    "Second-order convergence confirmed",
                    icon=":material/verified:",
                    color="green",
                )
            else:
                st.badge(
                    "Convergence check failed",
                    icon=":material/error:",
                    color="red",
                )
                st.error(
                    "The refinement study did not show decreasing error at the expected order.",
                    icon=":material/error:",
                )
            st.table(
                {
                    "Grid points": list(_CONVERGENCE_GRID_POINTS),
                    "Relative ground-state error": [
                        f"{error:.2e}" for error in convergence.relative_energy_errors
                    ],
                    "Observed order": [
                        "—",
                        *(f"{order:.2f}" for order in convergence.observed_orders),
                    ],
                },
                border="horizontal",
            )

st.caption(f"Quantum Playground v{__version__} · Python, NumPy, SciPy, Plotly, and Streamlit")
