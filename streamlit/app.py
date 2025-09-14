import streamlit as st

from utils import load_env


# Minimal landing page; all flow editing and running happens on the Prompts page.
st.set_page_config(page_title="Flow Builder", layout="wide")
load_env()

st.title("Flow Builder")
st.caption("Use the Prompts page to manage flows, edit prompts and per-step settings, and run flows from the sidebar.")

