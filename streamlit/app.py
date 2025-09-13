import streamlit as st

from utils import (
    load_env,
    get_default_model,
    generate,
    set_last_output,
    format_prompt,
    load_flow,
)


st.set_page_config(page_title="Content Generator", layout="wide")

# Ensure environment is loaded
load_env()

st.title("Content Generator")
st.caption("Customize the flow in Prompts → Flow Builder. Then run steps here.")

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

flow = load_flow()

col1, col2 = st.columns([1, 1])

with col1:
    run_all = st.button("Generate All", type="primary")
with col2:
    step_to_run = st.selectbox("Run single step", [f"{i+1}. {s['label']}" for i, s in enumerate(flow)])
    run_one = st.button("Run Selected")

# Store step outputs
if "flow_outputs" not in st.session_state:
    st.session_state["flow_outputs"] = {}

def run_step(idx: int) -> None:
    step = flow[idx]
    tmpl = step.get("template", "")
    out_key = step.get("output_key", f"step{idx+1}")
    variables = {"idea": idea, "notes": notes}
    variables.update(st.session_state.get("flow_outputs", {}))
    prompt_text = format_prompt(tmpl, variables)
    try:
        text = generate(provider, prompt_text, None, model, float(temperature), int(max_tokens), float(top_p))
        st.session_state["flow_outputs"][out_key] = text
        # Maintain legacy convenience keys for two-step flows
        if out_key.lower() == "outline":
            set_last_output("outline", text)
        if out_key.lower() in ("blog", "content"):
            set_last_output("content", text)
    except Exception as e:  # noqa: BLE001
        st.error(str(e))

if run_all:
    for i in range(len(flow)):
        run_step(i)

if run_one:
    idx = int(step_to_run.split(".")[0]) - 1
    run_step(idx)

st.subheader("Flow Outputs")
outs = st.session_state.get("flow_outputs", {})
if not outs:
    st.info("No outputs yet. Generate steps to see results.")
else:
    for i, step in enumerate(flow):
        key = step.get("output_key", f"step{i+1}")
        lbl = step.get("label", f"Step {i+1}")
        st.markdown(f"### {i+1}. {lbl} ({key})")
        st.code(outs.get(key, "<empty>"), language="markdown")
