import streamlit as st

from utils import (
    load_env,
    get_default_model,
    generate,
    set_last_output,
    load_prompts,
    format_prompt,
)


st.set_page_config(page_title="Content Generator", layout="wide")

# Ensure environment is loaded
load_env()

st.title("Content Generator")
st.caption("Enter an idea, generate an outline, then generate the blog.")

with st.sidebar:
    st.header("Model & Params")
    provider = st.radio("Provider", ["Groq", "Gemini"], index=0, horizontal=True)
    model = st.text_input("Model", value=get_default_model(provider))
    temperature = st.slider("Temperature", 0.0, 2.0, 0.7, 0.1)
    max_tokens = st.number_input("Max tokens", 1, 4000, 1200, 50)
    top_p = st.slider("Top P", 0.0, 1.0, 1.0, 0.05)

# Inputs
idea = st.text_input("Idea / Topic", value="Agentic AI for growth teams")
notes = st.text_area("Notes (optional)", height=100)

prompts = load_prompts()

col1, col2 = st.columns([1, 1])

with col1:
    run_outline = st.button("Generate Outline", type="primary")
with col2:
    run_blog = st.button("Generate Blog", disabled=not bool(st.session_state.get("last_outline")))

if run_outline:
    outline_prompt = format_prompt(prompts.get("outline", ""), {"idea": idea, "notes": notes})
    try:
        outline_text = generate(provider, outline_prompt, None, model, float(temperature), int(max_tokens), float(top_p))
        set_last_output("outline", outline_text)
    except Exception as e:  # noqa: BLE001
        st.error(str(e))

if run_blog and st.session_state.get("last_outline"):
    blog_prompt = format_prompt(
        prompts.get("blog", ""),
        {"idea": idea, "notes": notes, "outline": st.session_state.get("last_outline", "")},
    )
    try:
        blog_text = generate(provider, blog_prompt, None, model, float(temperature), int(max_tokens), float(top_p))
        set_last_output("content", blog_text)
    except Exception as e:  # noqa: BLE001
        st.error(str(e))

st.subheader("Outline (latest)")
st.code(st.session_state.get("last_outline", "No outline yet."), language="markdown")

st.subheader("Blog (latest)")
st.code(st.session_state.get("last_content", "No blog generated yet."), language="markdown")
