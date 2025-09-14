import streamlit as st

from utils import load_env, load_flows, save_flows, get_default_model, format_prompt, generate

try:
    from streamlit_agraph import agraph, Node, Edge, Config  # type: ignore
    HAVE_AGRAPH = True
except Exception:  # pragma: no cover
    HAVE_AGRAPH = False


st.set_page_config(page_title="Flow Builder", layout="wide")

load_env()

st.title("Flow Builder")
st.caption("Manage flows. Click a node to edit its prompt and model settings. Connect nodes to define order.")

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

_current = next((f for f in flows if f.get("name") == sel), flows[0] if flows else {"name": "Blog", "steps": []})
current = _current
steps = current.setdefault("steps", [])
graph = current.setdefault("graph", {})
nodes = graph.setdefault("nodes", [])
edges = graph.setdefault("edges", [])

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

existing_keys = [s.get("output_key", f"step{idx+1}") for idx, s in enumerate(steps)]

# Selected node state
if "selected_node_idx" not in st.session_state:
    st.session_state["selected_node_idx"] = 0 if steps else -1
sel_idx = st.session_state["selected_node_idx"]

def downstream_defaults(i: int) -> list[str]:
    # Build default downstream connections from edges if present
    key = steps[i].get("output_key", f"step{i+1}")
    # Map node ids by key if nodes cohort exists
    key_to_id = {n.get("output_key", existing_keys[idx]): int(n.get("id", idx+1)) for idx, n in enumerate(nodes)}
    id_to_key = {v: k for k, v in key_to_id.items()}
    sid = key_to_id.get(key)
    outs: list[str] = []
    if sid is not None:
        for e in edges:
            if int(e.get("source", -1)) == sid:
                k = id_to_key.get(int(e.get("target", -1)))
                if k:
                    outs.append(k)
    return outs

# Node palette (compact boxes)
st.subheader("Nodes")
if steps:
    cols = st.columns(4)
    for i, step in enumerate(steps):
        c = cols[i % 4]
        with c:
            with st.container(border=True):
                lbl = step.get("label", f"Step {i+1}")
                keyv = step.get("output_key", f"step{i+1}")
                st.markdown(f"**{i+1}. {lbl}**\n\n`{keyv}`")
                bcols = st.columns([1,1,1])
                with bcols[0]:
                    if st.button("Select", key=f"sel_{i}"):
                        st.session_state["selected_node_idx"] = i
                        st.rerun()
                with bcols[1]:
                    if st.button("Up", key=f"up_{i}"):
                        move_item(i, -1)
                        st.rerun()
                with bcols[2]:
                    if st.button("Down", key=f"down_{i}"):
                        move_item(i, +1)
                        st.rerun()
                if st.button("Delete", key=f"del_{i}"):
                    delete_item(i)
                    if sel_idx == i:
                        st.session_state["selected_node_idx"] = -1
                    st.rerun()
else:
    st.info("No nodes yet. Click Add Step to create one.")

st.divider()

# Detail editor for selected node
st.subheader("Selected Node")
if 0 <= sel_idx < len(steps):
    step = steps[sel_idx]
    st.markdown(f"Editing node #{sel_idx+1}")
    cols = st.columns([3,2])
    with cols[0]:
        step["label"] = st.text_input("Label", value=step.get("label", f"Step {sel_idx+1}"), key=f"label_{sel_idx}")
        step["output_key"] = st.text_input("Output key", value=step.get("output_key", f"step{sel_idx+1}"), key=f"key_{sel_idx}")
        step["template"] = st.text_area("Prompt template", value=step.get("template", ""), height=220, key=f"tmpl_{sel_idx}")
    with cols[1]:
        step["provider"] = st.selectbox("Provider", ["Groq", "Gemini"], index=0 if step.get("provider", "Groq") == "Groq" else 1, key=f"prov_{sel_idx}")
        step["model"] = st.text_input("Model", value=step.get("model", get_default_model(step.get("provider", "Groq"))), key=f"model_{sel_idx}")
        step["temperature"] = float(st.number_input("Temperature", min_value=0.0, max_value=2.0, value=float(step.get("temperature", 0.7)), step=0.1, key=f"temp_{sel_idx}"))
        step["top_p"] = float(st.number_input("Top P", min_value=0.0, max_value=1.0, value=float(step.get("top_p", 1.0)), step=0.05, key=f"topp_{sel_idx}"))
        step["max_tokens"] = int(st.number_input("Max tokens", min_value=1, max_value=4000, value=int(step.get("max_tokens", 1200)), step=50, key=f"maxtok_{sel_idx}"))
    # Connections
    step.setdefault("connect_to", downstream_defaults(sel_idx))
    step["connect_to"] = st.multiselect(
        "Connect to (downstream)",
        options=[k for k in existing_keys if k != step.get("output_key", f"step{sel_idx+1}")],
        default=step.get("connect_to", []),
        key=f"connect_{sel_idx}",
        help="Choose which steps depend on this step's output.",
    )
else:
    st.info("Select a node to edit its details.")

# Visual graph preview (optional)
st.divider()
st.subheader("Graph Preview")
if HAVE_AGRAPH and steps:
    # Build nodes/edges for preview
    key_to_idx = {s.get("output_key", f"step{i+1}"): i for i, s in enumerate(steps)}
    g_nodes = []
    g_edges = []
    for i, s in enumerate(steps):
        label = s.get("label", f"Step {i+1}")
        key = s.get("output_key", f"step{i+1}")
        g_nodes.append(Node(id=key, label=f"{i+1}. {label}\n({key})"))
        for tgt in s.get("connect_to", []) or []:
            if tgt in key_to_idx:
                g_edges.append(Edge(source=key, target=tgt))
    config = Config(width=900, height=400, directed=True, physics=False)
    agraph(nodes=g_nodes, edges=g_edges, config=config)
else:
    st.info("Install optional dependency 'streamlit-agraph' to see a live graph preview (pip install streamlit-agraph).")

st.divider()
cols = st.columns([1, 1, 2])
with cols[0]:
    if st.button("Add Step", type="secondary"):
        add_item()
        save_flows(data)
        st.rerun()
with cols[1]:
    if st.button("Save Flow", type="primary"):
        # Materialize a graph from connect_to fields
        # Node ids are positional for now
        nodes = []
        for idx, s in enumerate(steps):
            nd = {
                "id": idx + 1,
                "label": s.get("label", f"Step {idx+1}"),
                "output_key": s.get("output_key", f"step{idx+1}"),
                "template": s.get("template", ""),
                "provider": s.get("provider", "Groq"),
                "model": s.get("model", get_default_model(s.get("provider", "Groq"))),
                "temperature": float(s.get("temperature", 0.7)),
                "max_tokens": int(s.get("max_tokens", 1200)),
                "top_p": float(s.get("top_p", 1.0)),
            }
            nodes.append(nd)
        key_to_id = {n["output_key"]: n["id"] for n in nodes}
        edges = []
        for idx, s in enumerate(steps):
            src_id = idx + 1
            for tgt_key in s.get("connect_to", []) or []:
                if tgt_key in key_to_id:
                    edges.append({"source": src_id, "target": key_to_id[tgt_key]})
        current["graph"] = {"nodes": nodes, "edges": edges}
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
