"""Streamlit entrypoint for Quantum Playground."""

import streamlit as st

from quantum_playground import __version__
from quantum_playground.figures import (
    StateQuantity,
    build_stationary_state_figure,
    build_tunneling_motion_figure,
)
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
from quantum_playground.solver import SolverError, solve
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
    "visualization_mode": "Stationary state",
    "tunneling_cycle": 0.0,
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
    "visualization_mode",
)
_CONVERGENCE_GRID_POINTS = (201, 401, 801)
_STATIONARY_VIEW = "Stationary state"
_TUNNELING_VIEW = "Tunneling motion"


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
    for key in ("state_number", "show_density", "tunneling_cycle"):
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
        "Observed": [_scientific_math(observed) for _, observed, _, _ in checks],
        "Limit": [_scientific_math(limit, decimals=1, prefix=r"\le") for _, _, limit, _ in checks],
        "Status": [
            ":green-badge[Pass]" if passed else ":red-badge[Fail]" for _, _, _, passed in checks
        ],
    }


def _scientific_math(value: float, *, decimals: int = 2, prefix: str = "") -> str:
    coefficient, exponent = f"{value:.{decimals}e}".split("e")
    prefix_text = f"{prefix} " if prefix else ""
    return rf"${prefix_text}{coefficient} \times 10^{{{int(exponent)}}}$"


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
    state_help = r"State $n$ has $n-1$ internal nodes and an energy proportional to $n^2$."
elif experiment is ExperimentId.HARMONIC_OSCILLATOR:
    preset = HARMONIC_OSCILLATOR_PRESET
    try_this = (
        r"Raise $\omega$ and watch the evenly spaced energy ladder expand while the state "
        "contracts "
        "toward the center."
    )
    state_help = r"Displayed state $k$ corresponds to oscillator quantum number $n=k-1$."
else:
    preset = DOUBLE_WELL_PRESET
    try_this = (
        r"Raise either control and watch $\Delta E_{01}$ collapse as the lowest tunneling "
        "pair becomes "
        "nearly degenerate."
    )
    state_help = "States 1 and 2 are the even/odd tunneling pair; higher states add nodes."

st.header(preset.title)
st.markdown(f"{preset.description} **Try this:** {try_this}")
is_tunneling_motion = False
tunneling_cycle = 0.0
if experiment is ExperimentId.DOUBLE_WELL:
    st.markdown("**Choose how to explore**")
    _load_dynamic_control("visualization_mode")
    visualization_mode = st.segmented_control(
        "Visualization",
        (_STATIONARY_VIEW, _TUNNELING_VIEW),
        key="visualization_mode",
        help=(
            "Inspect individual stationary states or scrub through a localized superposition "
            "of the lowest even and odd states."
        ),
        on_change=_store_dynamic_control,
        args=("visualization_mode",),
    )
    is_tunneling_motion = visualization_mode == _TUNNELING_VIEW
else:
    st.markdown("**Explore this state**")
st.caption("Results update automatically when you change a control.")

if is_tunneling_motion:
    state_number = 1
    show_density = True
    show_baseline = False
    tunneling_cycle = st.slider(
        r"Tunneling cycle $t/T$",
        min_value=0.0,
        max_value=1.0,
        step=0.025,
        key="tunneling_cycle",
        help=(
            "0: localized in the starting well · ¼: balanced · ½: opposite well · "
            "1: back to the start."
        ),
    )
    st.caption("Drag through one full cycle: start → balanced → opposite well → return.")
else:
    control_widths = (3, 2, 2) if experiment is ExperimentId.DOUBLE_WELL else (3, 2)
    control_columns = st.columns(control_widths, vertical_alignment="bottom")
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
            help=(
                r"Switch from the signed wavefunction $\psi(x)$ to the measurable density "
                r"$|\psi(x)|^2$."
            ),
            wrap=True,
        )
    if experiment is ExperimentId.DOUBLE_WELL:
        with control_columns[2]:
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
except SolverError:
    result_slot.error(
        "The numerical solver could not complete this experiment. "
        "Try resetting the experiment or moving the controls toward their defaults.",
        icon=":material/error:",
    )
    st.stop()
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
figure = (
    build_tunneling_motion_figure(result, cycle_position=float(tunneling_cycle))
    if is_tunneling_motion
    else build_stationary_state_figure(
        result,
        state_index=selected_index,
        quantity=quantity,
        comparison_result=comparison_result,
    )
)
if is_tunneling_motion:
    tunneling_period = float(figure.layout.meta["tunneling_period"])
    left_probability = float(figure.layout.meta["left_probability"])
    right_probability = float(figure.layout.meta["right_probability"])

with result_slot:
    if experiment is ExperimentId.DOUBLE_WELL:
        splitting = float(result.energies[1] - result.energies[0])
        splitting_delta = None
        if comparison_result is not None:
            reference_splitting = float(
                comparison_result.energies[1] - comparison_result.energies[0]
            )
            splitting_delta = f"{100.0 * (splitting / reference_splitting - 1.0):+.1f}%"
        metric_columns = st.columns(3)
        with metric_columns[0]:
            st.metric(
                r"Energy split $\Delta E_{01}$",
                f"{splitting:.3g}",
                delta=splitting_delta,
                delta_color="off",
                delta_arrow="off",
                delta_description="vs default" if comparison_result is not None else None,
                help="Energy gap between the even ground state and odd first excited state.",
                border=True,
            )
        if is_tunneling_motion:
            with metric_columns[1]:
                st.metric(
                    "Left probability",
                    f"{left_probability:.1%}",
                    help="Integrated probability density on the left half of the domain.",
                    border=True,
                )
            with metric_columns[2]:
                st.metric(
                    r"Period $T$",
                    f"{tunneling_period:.2f}",
                    help="One complete left-to-right-to-left cycle in dimensionless time.",
                    border=True,
                )
        else:
            with metric_columns[1]:
                st.metric(
                    f"Selected energy $E_{{{state_number}}}$",
                    f"{result.energies[selected_index]:.5f}",
                    border=True,
                )
            with metric_columns[2]:
                st.metric(
                    "Solve time",
                    f"{result.solve_time_seconds * 1_000:.0f} ms",
                    border=True,
                )
    else:
        with st.container(horizontal=True, gap="small"):
            st.metric(
                f"Selected energy $E_{{{state_number}}}$",
                f"{result.energies[selected_index]:.5f}",
                border=True,
            )
            st.metric(
                "Analytic energy error",
                _scientific_math(report.relative_energy_errors[selected_index]),
                border=True,
            )
            st.metric(
                "Solve time",
                f"{result.solve_time_seconds * 1_000:.0f} ms",
                border=True,
            )

    st.plotly_chart(
        figure,
        key="tunneling_motion_figure" if is_tunneling_motion else "stationary_state_figure",
        width="stretch",
        theme=None,
        config={"displaylogo": False, "scrollZoom": False, "responsive": True},
    )
    if experiment is ExperimentId.INFINITE_WELL:
        simulation_summary = rf"across a width $L = {well_width:.1f}$"
    elif experiment is ExperimentId.HARMONIC_OSCILLATOR:
        simulation_summary = rf"on $x \in [-8, 8]$ with $\omega = {oscillator_omega:.1f}$"
    else:
        simulation_summary = (
            rf"on $x \in [-6, 6]$ with $V_0 = {double_well_barrier_height:.1f}$ and "
            rf"$d = {double_well_separation:.1f}$"
        )
    figure_note = (
        "The cycle view shows the true normalized density of an equal two-state superposition."
        if is_tunneling_motion
        else "The upper state profile is display-scaled; the lower panel shows its true values."
    )
    st.caption(
        f"Solved {result.config.eigenstate_count} states on "
        f"{result.config.grid_points:,} grid points {simulation_summary} in "
        f"{result.solve_time_seconds * 1_000:.0f} ms. {figure_note}"
    )
    if comparison_result is not None:
        reference_splitting = float(comparison_result.energies[1] - comparison_result.energies[0])
        st.caption(
            rf"The default reference is fixed at $V_0 = {BARRIER_HEIGHT.default:.1f}$ and "
            rf"$d = {WELL_SEPARATION.default:.1f}$ "
            rf"($\Delta E_{{01}} = {reference_splitting:.6f}$). Dashed "
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

if is_tunneling_motion:
    explanation_title = "Why the particle tunnels"
elif show_density:
    explanation_title = "Reading the probability density"
else:
    explanation_title = "Reading the wavefunction"
with st.container(border=True):
    st.subheader(explanation_title, icon=":material/lightbulb:")
    if is_tunneling_motion:
        st.markdown(
            "The cycle begins with a **localized superposition** of the lowest even and odd "
            r"stationary states. Their relative phase evolves at the energy splitting "
            r"$\Delta E_{01}$, moving "
            "the probability density between the wells without changing its normalization."
        )
        st.markdown(
            rf"After **half a period** the density reaches the opposite well; after "
            rf"$T = 2\pi/\Delta E_{{01}} = {tunneling_period:.2f}$ it returns to its starting side."
        )
        st.caption(
            rf"At $t/T = {tunneling_cycle:.3f}$: $P_L = {left_probability:.1%}$ · "
            rf"$P_R = {right_probability:.1%}$."
        )
    elif experiment is ExperimentId.INFINITE_WELL:
        st.markdown(
            rf"State $n = {state_number}$ has **{state_number - 1} internal nodes**. Its energy "
            r"is proportional to $n^2$, so higher states spread farther apart on the energy axis."
        )
    elif experiment is ExperimentId.HARMONIC_OSCILLATOR:
        oscillator_index = int(state_number) - 1
        st.markdown(
            rf"Displayed state **{state_number}** is oscillator state $n = {oscillator_index}$ "
            f"and has **{oscillator_index} internal nodes**. Adjacent energies are evenly spaced "
            rf"by $\Delta E = \omega = {oscillator_omega:.1f}$, including the nonzero "
            "ground-state energy."
        )
    else:
        parity = "even" if selected_index % 2 == 0 else "odd"
        st.markdown(
            f"Displayed state **{state_number}** has **{parity} parity**. The lowest even and odd "
            rf"states form a tunneling pair with $\Delta E_{{01}} = {splitting:.6f}$; a smaller "
            "split means "
            "the particle exchanges between the wells more slowly."
        )
    if not is_tunneling_motion:
        if show_density:
            st.markdown(
                "The probability density is never negative. Peaks mark positions where the "
                "particle is more likely to be found; nodes remain positions of zero probability."
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
        boundary_description = r"$\psi = 0$ at both walls"
        state_labels = [f"$n = {index}$" for index in range(1, result.config.eigenstate_count + 1)]
    elif experiment is ExperimentId.HARMONIC_OSCILLATOR:
        st.latex(r"V(x)=\frac{1}{2}\omega^2x^2,\qquad E_n=\omega(n+\tfrac{1}{2})")
        boundary_description = (
            r"finite-domain approximation on $x \in [-8, 8]$, with $\psi = 0$ at both endpoints"
        )
        state_labels = [
            f"$n = {index}$ (state {index + 1})" for index in range(result.config.eigenstate_count)
        ]
    else:
        st.latex(r"V(x)=V_0\left[\left(\frac{2x}{d}\right)^2-1\right]^2")
        boundary_description = r"finite domain $x \in [-6, 6]$, with $\psi = 0$ at both endpoints"
        state_labels = [
            f"state {index + 1} · {'even' if index % 2 == 0 else 'odd'}"
            for index in range(result.config.eigenstate_count)
        ]
    grid_spacing = float(result.x[1] - result.x[0])
    grid_spacing_math = _scientific_math(grid_spacing, decimals=3, prefix=r"\Delta x =")
    st.caption(
        f"Grid: {result.config.grid_points:,} points with {grid_spacing_math}. "
        rf"Dimensionless units: $\hbar = m = 1$. Boundary: {boundary_description}."
    )
    if experiment is ExperimentId.DOUBLE_WELL:
        st.caption(r"The minima lie at $x = \pm d/2$ and the central barrier is $V(0) = V_0$.")

    st.markdown("**Current-run checks**")
    st.table(_diagnostic_evidence(diagnostic_checks), border="horizontal")

    st.markdown("**Energy spectrum**")
    if report is not None:
        st.table(
            {
                "State": state_labels,
                "Numerical E": [f"{energy:.7f}" for energy in result.energies],
                "Exact E": [f"{energy:.7f}" for energy in report.analytic_energies],
                "Relative error": [
                    _scientific_math(error) for error in report.relative_energy_errors
                ],
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
                        _scientific_math(error) for error in convergence.relative_energy_errors
                    ],
                    "Observed order": [
                        "—",
                        *(f"{order:.2f}" for order in convergence.observed_orders),
                    ],
                },
                border="horizontal",
            )

st.caption(
    f"Quantum Playground v{__version__} · Python, NumPy, SciPy, Plotly, and Streamlit · "
    "[View source on GitHub](https://github.com/sebasalonsogp/Quantum-Playground)"
)
