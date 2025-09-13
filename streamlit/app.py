import streamlit as st

from utils import (
    load_env,
    generate,
    set_last_output,
    format_prompt,
    load_flows,
    get_active_flow,
    get_execution_sequence,
)


st.set_page_config(page_title="Content Generator", layout="wide")

# Ensure environment is loaded
load_env()

st.title("Content Generator")
st.caption("Customize the flow in Prompts → Flow Builder. Then run steps here.")

with st.sidebar:
    st.header("Run")
    st.caption("Uses per-step settings from the active flow.")
    run_all = st.button("Generate All", type="primary")
    _, active_flow = get_active_flow()
    seq = get_execution_sequence(active_flow)
    step_opts = [f"{i+1}. {s.get('label','Step')}" for i, s in enumerate(seq)]
    sel = st.selectbox("Run single step", step_opts)
    run_one = st.button("Run Selected")

# Inputs (shared variables for prompts)
idea = st.text_input("Idea / Topic", value="Agentic AI for growth teams")
notes = st.text_area("Notes (optional)", height=100)

_, flow = get_active_flow()
seq = get_execution_sequence(flow)

# Store step outputs
if "flow_outputs" not in st.session_state:
    st.session_state["flow_outputs"] = {}

def run_step(idx: int) -> None:
    step = seq[idx]
    tmpl = step.get("template", "")
    out_key = step.get("output_key", f"step{idx+1}")
    variables = {"idea": idea, "notes": notes}
    variables.update(st.session_state.get("flow_outputs", {}))
    prompt_text = format_prompt(tmpl, variables)
    # Use per-step params
    provider = step.get("provider", "Groq")
    model = step.get("model") or None
    temperature = float(step.get("temperature", 0.7))
    max_tokens = int(step.get("max_tokens", 1200))
    top_p = float(step.get("top_p", 1.0))
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
    for i in range(len(seq)):
        run_step(i)

if run_one:
    idx = int(sel.split(".")[0]) - 1
    run_step(idx)

st.subheader("Flow Outputs")
outs = st.session_state.get("flow_outputs", {})
if not outs:
    st.info("No outputs yet. Generate steps to see results.")
else:
    for i, step in enumerate(seq):
        key = step.get("output_key", f"step{i+1}")
        lbl = step.get("label", f"Step {i+1}")
        st.markdown(f"### {i+1}. {lbl} ({key})")
        st.code(outs.get(key, "<empty>"), language="markdown")
