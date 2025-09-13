import streamlit as st

from utils import load_env, load_prompts, save_prompts


st.set_page_config(page_title="Prompt Manager", layout="wide")

load_env()

st.title("Prompt Manager")
st.caption("Configure base templates for Outline and Blog generation.")

prompts = load_prompts()

st.subheader("Outline Template")
outline_t = st.text_area(
    "Template",
    value=prompts.get("outline", ""),
    height=220,
    help="Variables: {idea}, {notes}",
)

st.subheader("Blog Template")
blog_t = st.text_area(
    "Template",
    value=prompts.get("blog", ""),
    height=300,
    help="Variables: {idea}, {notes}, {outline}",
)

if st.button("Save Templates", type="primary"):
    try:
        save_prompts({"outline": outline_t, "blog": blog_t})
        st.success("Templates saved.")
    except Exception as e:  # noqa: BLE001
        st.error(str(e))

