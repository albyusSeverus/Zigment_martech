import streamlit as st

from utils import load_env, load_flows, save_flows, get_default_model, format_prompt, generate


st.set_page_config(page_title="Flow Builder", layout="wide")

load_env()

st.title("Flow Builder")
st.caption("Manage multiple flows. Edit steps with per-step model settings. Run the flow from the sidebar.")

if "flows_state" not in st.session_state:
    st.session_state["flows_state"] = load_flows()

data = st.session_state["flows_state"]
flows = data.get("flows", [])
active = data.get("active", "Blog")

# Sidebar: run controls
curr_flow_sidebar = next((f for f in flows if f.get("name") == active), (flows[0] if flows else {"steps": []}))

with st.sidebar:
    st.header("Run Flow")
    idea = st.text_input("Idea / Topic", value="Agentic AI for growth teams", key="idea_fb")
    notes = st.text_area("Notes (optional)", height=100, key="notes_fb")
    run_all = st.button("Generate All", type="primary", key="run_all_fb")
    step_opts = [f"{i+1}. {s['label']}" for i, s in enumerate(curr_flow_sidebar.get("steps", []))] if flows else []
    selected = st.selectbox("Run single step", step_opts, key="sel_step_fb")
    run_one = st.button("Run Selected", key="run_one_fb")

# Flow selection and CRUD
flow_names = [f.get("name", f"Flow{i+1}") for i, f in enumerate(flows)]
current_idx = max(0, flow_names.index(active)) if flow_names else 0
col_top = st.columns([3, 2, 2, 2, 2])
with col_top[0]:
    sel = st.selectbox("Select flow", flow_names, index=current_idx)
with col_top[1]:
    new_name = st.text_input("Rename", value=sel if flow_names else "Blog")
with col_top[2]:
    if st.button("Set Active"):
        data["active"] = new_name
        # Also rename the selected flow
        for f in flows:
            if f.get("name") == sel:
                f["name"] = new_name
                f["label"] = new_name
        save_flows(data)
        st.success("Active flow updated.")
with col_top[3]:
    if st.button("Duplicate"):
        src = next((f for f in flows if f.get("name") == sel), None)
        if src:
            dup = {"name": f"{src['name']}-copy", "label": f"{src['label']} (copy)", "steps": [dict(s) for s in src.get("steps", [])]}
            flows.append(dup)
            save_flows(data)
            st.rerun()
with col_top[4]:
    if st.button("New Flow"):
        flows.append({"name": f"Flow{len(flows)+1}", "label": f"Flow {len(flows)+1}", "steps": []})
        save_flows(data)
        st.rerun()

# Current editable flow
current = next((f for f in flows if f.get("name") == sel), flows[0] if flows else {"name": "Blog", "steps": []})
steps = current.setdefault("steps", [])

st.markdown("Variables: `{idea}`, `{notes}`, plus outputs of prior steps by their output key (e.g., `{outline}`).")

def move_item(idx: int, direction: int) -> None:
    j = idx + direction
    if 0 <= j < len(steps):
        steps[idx], steps[j] = steps[j], steps[idx]

def delete_item(idx: int) -> None:
    del steps[idx]

def add_item() -> None:
    steps.append({
        "label": "New Step",
        "output_key": f"step{len(steps)+1}",
        "template": "Write something about {idea} using {notes}.",
        "provider": "Groq",
        "model": get_default_model("Groq"),
        "temperature": 0.7,
        "max_tokens": 1200,
        "top_p": 1.0,
    })

for i, step in enumerate(steps):
    with st.container(border=True):
        cols = st.columns([5, 1, 1, 1])
        with cols[0]:
            step["label"] = st.text_input(f"Label #{i+1}", value=step.get("label", "Step"), key=f"label_{i}")
        with cols[1]:
            if st.button("Up", key=f"up_{i}"):
                move_item(i, -1)
                st.rerun()
        with cols[2]:
            if st.button("Down", key=f"down_{i}"):
                move_item(i, +1)
                st.rerun()
        with cols[3]:
            if st.button("Delete", key=f"del_{i}"):
                delete_item(i)
                st.rerun()

        step["output_key"] = st.text_input("Output key", value=step.get("output_key", f"step{i+1}"), key=f"key_{i}")
        step["template"] = st.text_area(
            "Prompt template",
            value=step.get("template", ""),
            height=160,
            key=f"tmpl_{i}",
        )
        pcols = st.columns([2, 3, 1, 1, 1])
        with pcols[0]:
            step["provider"] = st.selectbox("Provider", ["Groq", "Gemini"], index=0 if step.get("provider", "Groq") == "Groq" else 1, key=f"prov_{i}")
        with pcols[1]:
            step["model"] = st.text_input("Model", value=step.get("model", get_default_model(step.get("provider", "Groq"))), key=f"model_{i}")
        with pcols[2]:
            step["temperature"] = float(st.number_input("Temp", min_value=0.0, max_value=2.0, value=float(step.get("temperature", 0.7)), step=0.1, key=f"temp_{i}"))
        with pcols[3]:
            step["top_p"] = float(st.number_input("TopP", min_value=0.0, max_value=1.0, value=float(step.get("top_p", 1.0)), step=0.05, key=f"topp_{i}"))
        with pcols[4]:
            step["max_tokens"] = int(st.number_input("MaxTok", min_value=1, max_value=4000, value=int(step.get("max_tokens", 1200)), step=50, key=f"maxtok_{i}"))

st.divider()
cols = st.columns([1, 1, 2])
with cols[0]:
    if st.button("Add Step", type="secondary"):
        add_item()
        save_flows(data)
        st.rerun()
with cols[1]:
    if st.button("Save Flow", type="primary"):
        save_flows(data)
        st.success("Flow saved.")

# Run logic (uses per-step params)
if "flow_outputs_fb" not in st.session_state:
    st.session_state["flow_outputs_fb"] = {}

def run_step(idx: int) -> None:
    s = steps[idx]
    variables = {"idea": idea, "notes": notes}
    variables.update(st.session_state.get("flow_outputs_fb", {}))
    prompt_text = format_prompt(s.get("template", ""), variables)
    try:
        text = generate(
            s.get("provider", "Groq"),
            prompt_text,
            None,
            s.get("model", get_default_model(s.get("provider", "Groq"))),
            float(s.get("temperature", 0.7)),
            int(s.get("max_tokens", 1200)),
            float(s.get("top_p", 1.0)),
        )
        st.session_state["flow_outputs_fb"][s.get("output_key", f"step{idx+1}")] = text
    except Exception as e:  # noqa: BLE001
        st.error(str(e))

steps_for_run = curr_flow_sidebar.get("steps", [])

if run_all and steps_for_run:
    for i in range(len(steps_for_run)):
        run_step(i)

if run_one and steps_for_run:
    try:
        idx = int(str(selected).split(".")[0]) - 1
        if 0 <= idx < len(steps_for_run):
            run_step(idx)
    except Exception:
        pass

if st.session_state.get("flow_outputs_fb"):
    st.subheader("Session Outputs")
    for i, s in enumerate(steps):
        key = s.get("output_key", f"step{i+1}")
        st.markdown(f"### {i+1}. {s.get('label', f'Step {i+1}')} ({key})")
        st.code(st.session_state["flow_outputs_fb"].get(key, "<empty>"), language="markdown")
