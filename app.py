"""Streamlit entrypoint for Quantum Playground."""

import streamlit as st

from quantum_playground import __version__

st.set_page_config(
    page_title="Quantum Playground",
    page_icon="⚛️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.title("Quantum Playground")
st.caption("Interactive numerical experiments for one-dimensional quantum systems.")

with st.container(border=True):
    st.subheader("The playground is taking shape")
    st.write(
        "The project foundation is ready. The first implementation milestone will validate "
        "an infinite-square-well solver against its analytic solution before interactive "
        "experiments are added."
    )

st.caption(f"Scaffold version {__version__}")
